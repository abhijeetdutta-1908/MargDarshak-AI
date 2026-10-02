"""Nearby places: Google Places API (New) when a key is set, otherwise the seeded catalogue."""

import logging
import re

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.ml.recommendation import haversine_km
from app.models import Destination, Place
from app.services.http import ExternalAPIError, request_json
from app.utils.cache import TTLCache

log = logging.getLogger("margdarshak")
NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
FIELDS = "places.id,places.displayName,places.rating,places.formattedAddress,places.location,places.primaryType,places.photos"
GOOGLE_TYPES = {
    "attraction": ["tourist_attraction", "museum"],
    "restaurant": ["restaurant"],
    "shopping": ["shopping_mall", "market"],
    "activity": ["park", "amusement_park"],
}
PHOTO_NAME = re.compile(r"^places/[A-Za-z0-9_-]+/photos/[A-Za-z0-9_-]+$")

_cache = TTLCache(get_settings().places_cache_seconds)


def seeded_places(db: Session, dest: Destination, kind: str | None, center: tuple[float, float]) -> list[dict]:
    stmt = select(Place).where(Place.destination_id == dest.id)
    if kind:
        stmt = stmt.where(Place.kind == kind)
    items = [
        {
            "id": p.id,
            "external_id": None,
            "name": p.name,
            "kind": p.kind,
            "category": p.kind,
            "tags": p.tags,
            "description": p.description,
            "rating": p.rating,
            "address": p.address or dest.name,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "distance_km": round(haversine_km(center, (p.latitude, p.longitude)), 1),
            "estimated_cost": p.estimated_cost,
            "duration_minutes": p.duration_minutes,
            "is_indoor": p.is_indoor,
            "photo": None,
        }
        for p in db.scalars(stmt)
    ]
    return sorted(items, key=lambda x: x["distance_km"])


async def google_places(client: httpx.AsyncClient, key: str, kind: str, center: tuple[float, float]) -> list[dict]:
    body = {
        "includedTypes": GOOGLE_TYPES[kind],
        "maxResultCount": 15,
        "locationRestriction": {"circle": {"center": {"latitude": center[0], "longitude": center[1]}, "radius": 10000.0}},
    }
    data = await request_json(client, "POST", NEARBY_URL, "Google Places", json=body,
                              headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS})
    out = []
    for p in data.get("places", []):
        loc = p.get("location", {})
        if "latitude" not in loc:
            continue
        photo = (p.get("photos") or [{}])[0].get("name")
        out.append({
            "id": None,
            "external_id": p.get("id"),
            "name": p.get("displayName", {}).get("text", "Unnamed place"),
            "kind": kind,
            "category": (p.get("primaryType") or kind).replace("_", " "),
            "tags": [],
            "description": None,
            "rating": p.get("rating"),
            "address": p.get("formattedAddress"),
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "distance_km": round(haversine_km(center, (loc["latitude"], loc["longitude"])), 1),
            "estimated_cost": None,
            "duration_minutes": None,
            "is_indoor": None,
            # Served through our /api/places/photo proxy so the API key never reaches the browser.
            "photo": f"/api/places/photo?name={photo}" if photo and PHOTO_NAME.match(photo) else None,
        })
    return sorted(out, key=lambda x: x["distance_km"])


async def get_places(db: Session, client: httpx.AsyncClient, dest: Destination, kind: str | None,
                     center: tuple[float, float] | None = None) -> dict:
    center = center or (dest.latitude, dest.longitude)
    key = get_settings().places_key
    seeded = {"source": "seeded", "note": "Using curated destination data (Google Places not configured).",
              "items": seeded_places(db, dest, kind, center)}
    if not key or kind is None:
        if key and kind is None:
            seeded["note"] = "Choose a category to search Google Places; showing curated destination data."
        return seeded
    cache_key = (round(center[0], 3), round(center[1], 3), kind)
    if (hit := _cache.get(cache_key)) is not None:
        return hit
    try:
        items = await google_places(client, key, kind, center)
    except ExternalAPIError as e:
        log.warning("Google Places failed for %s: %s", dest.name, e.reason)
        seeded["note"] = f"Google Places unavailable ({e.reason}); using curated destination data."
        return seeded
    result = {"source": "google_places", "note": None, "items": items}
    _cache.set(cache_key, result)
    return result


async def fetch_photo(client: httpx.AsyncClient, name: str, max_width: int = 800) -> tuple[bytes, str]:
    key = get_settings().places_key
    if not key or not PHOTO_NAME.match(name):
        raise ExternalAPIError("Photo not available")
    try:
        r = await client.get(f"https://places.googleapis.com/v1/{name}/media",
                             params={"maxWidthPx": max_width, "key": key}, follow_redirects=True)
    except httpx.HTTPError:
        raise ExternalAPIError("Google Places is unreachable") from None
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
        raise ExternalAPIError("Photo not available")
    return r.content, r.headers["content-type"]
