import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.ml.route import RouteOptimizer
from app.schemas.preferences import Transport
from app.services import maps, places, weather
from app.services.catalog import get_destination
from app.services.http import ExternalAPIError, get_http

router = APIRouter()


@router.get("/api/weather/{destination_id}", tags=["weather"])
async def get_weather(destination_id: int, db: Session = Depends(get_db), http: httpx.AsyncClient = Depends(get_http)):
    """Current weather and 5-day forecast. `source` is `live` (OpenWeather) or `fallback` (seasonal guidance)."""
    return await weather.get_weather(http, get_destination(db, destination_id))


@router.get("/api/places/photo", tags=["places"], include_in_schema=False)
async def place_photo(name: str = Query(max_length=300), http: httpx.AsyncClient = Depends(get_http)):
    try:
        content, ctype = await places.fetch_photo(http, name)
    except ExternalAPIError as e:
        raise HTTPException(404, e.reason) from None
    return Response(content, media_type=ctype, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/api/places/{destination_id}", tags=["places"])
async def get_places(
    destination_id: int,
    kind: str | None = Query(None, pattern="^(attraction|restaurant|shopping|activity)$"),
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
    http: httpx.AsyncClient = Depends(get_http),
):
    """Nearby attractions, restaurants, shopping and activities, sorted by distance.

    `source` is `google_places` when a key is configured, otherwise `seeded` (curated dataset).
    """
    dest = get_destination(db, destination_id)
    center = (lat, lng) if lat is not None and lng is not None else None
    return await places.get_places(db, http, dest, kind, center)


class RoutePoint(BaseModel):
    name: str = Field(max_length=160)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RouteRequest(BaseModel):
    points: list[RoutePoint] = Field(min_length=2, max_length=25)
    start_index: int = Field(0, ge=0)
    return_to_start: bool = False
    transport: Transport | None = "mixed"


@router.post("/api/routes/optimize", tags=["routes"])
async def optimize_route(req: RouteRequest, http: httpx.AsyncClient = Depends(get_http)):
    """Reorder stops to minimise travel (nearest-neighbour + 2-opt over a distance matrix)."""
    if req.start_index >= len(req.points):
        raise HTTPException(422, "start_index is outside the list of points")
    coords = [(p.latitude, p.longitude) for p in req.points]
    matrix = await maps.distance_matrix(http, coords, req.transport or "mixed")
    result = RouteOptimizer(matrix["km"], matrix["minutes"], req.start_index, req.return_to_start).optimize()
    return {
        **result,
        "stops": [req.points[i].model_dump() for i in result["order"]],
        "distance_source": matrix["source"],
        "note": matrix["note"],
    }


@router.get("/api/config", tags=["system"])
def public_config():
    """Non-secret settings the frontend needs. The browser Maps key is a separate, referrer-restricted key."""
    s = get_settings()
    return {
        "maps": {"provider": "google" if s.google_maps_browser_key else "openstreetmap",
                 "browser_key": s.google_maps_browser_key or None},
        "live_weather": bool(s.openweather_api_key),
        "live_places": bool(s.places_key),
    }
