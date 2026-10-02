"""Travel distances/times between points: Google Routes API matrix, or a haversine estimate."""

import logging

import httpx

from app.config import get_settings
from app.ml.route import Point, estimate_matrix
from app.services.http import ExternalAPIError, request_json
from app.utils.cache import TTLCache

log = logging.getLogger("margdarshak")
MATRIX_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
MAX_GOOGLE_POINTS = 10
TRAVEL_MODE = {"public": "TRANSIT", "car": "DRIVE", "taxi": "DRIVE", "bike": "TWO_WHEELER", "mixed": "DRIVE", "walk": "WALK"}

_cache = TTLCache(6 * 3600)


async def google_matrix(client: httpx.AsyncClient, key: str, points: list[Point], mode: str):
    wp = [{"waypoint": {"location": {"latLng": {"latitude": la, "longitude": lo}}}} for la, lo in points]
    body = {"origins": wp, "destinations": wp, "travelMode": TRAVEL_MODE.get(mode, "DRIVE")}
    data = await request_json(client, "POST", MATRIX_URL, "Google Routes", json=body, headers={
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,duration,condition",
    })
    if isinstance(data, dict):  # error envelope instead of the element list
        raise ExternalAPIError("Google Routes returned an unexpected response")
    km, minutes = estimate_matrix(points, mode)  # fill any element Google can't route
    for el in data:
        i, j = el.get("originIndex", 0), el.get("destinationIndex", 0)
        if i != j and el.get("condition") == "ROUTE_EXISTS":
            km[i][j] = round(el.get("distanceMeters", 0) / 1000, 2)
            minutes[i][j] = round(int(str(el.get("duration", "0s")).rstrip("s") or 0) / 60, 1)
    return km, minutes


async def distance_matrix(client: httpx.AsyncClient, points: list[Point], mode: str = "mixed") -> dict:
    key = get_settings().google_maps_api_key
    if key and 2 <= len(points) <= MAX_GOOGLE_POINTS:
        cache_key = (tuple((round(a, 4), round(b, 4)) for a, b in points), mode)
        if (hit := _cache.get(cache_key)) is not None:
            return hit
        try:
            km, minutes = await google_matrix(client, key, points, mode)
            result = {"km": km, "minutes": minutes, "source": "google_routes", "note": None}
            _cache.set(cache_key, result)
            return result
        except ExternalAPIError as e:
            log.warning("Google Routes failed: %s", e.reason)
            note = f"Google Routes unavailable ({e.reason}); distances estimated."
    elif key:
        note = f"More than {MAX_GOOGLE_POINTS} stops; distances estimated to stay within API limits."
    else:
        note = "Distances estimated from coordinates (Google Maps not configured)."
    km, minutes = estimate_matrix(points, mode)
    return {"km": km, "minutes": minutes, "source": "estimate", "note": note}
