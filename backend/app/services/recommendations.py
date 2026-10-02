import logging
import threading
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.ml.recommendation import DestinationFeatures, Preferences, RecommendationEngine
from app.models import Destination, Hotel, Place
from app.schemas.recommendation import RecommendationRequest

log = logging.getLogger("margdarshak")

_lock = threading.Lock()
_engine: RecommendationEngine | None = None


def invalidate_catalog() -> None:
    """Call after destinations/places/hotels change so embeddings are rebuilt."""
    global _engine
    with _lock:
        _engine = None


def load_features(db: Session) -> list[DestinationFeatures]:
    place_tags = defaultdict(list)
    for dest_id, kind, tags in db.execute(select(Place.destination_id, Place.kind, Place.tags)):
        place_tags[dest_id].append(set(tags) | {kind})
    hotel_prices = defaultdict(lambda: defaultdict(list))
    for dest_id, tier, price in db.execute(select(Hotel.destination_id, Hotel.tier, Hotel.price_per_night)):
        hotel_prices[dest_id][tier].append(price)
    cols = [f for f in DestinationFeatures.__dataclass_fields__ if f not in ("place_tags", "hotel_prices")]
    return [
        DestinationFeatures(
            **{c: getattr(d, c) for c in cols},
            place_tags=place_tags[d.id],
            hotel_prices=dict(hotel_prices[d.id]),
        )
        for d in db.scalars(select(Destination).order_by(Destination.id))
    ]


def get_engine(db: Session) -> RecommendationEngine:
    global _engine
    with _lock:
        if _engine is None:
            features = load_features(db)
            if not features:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "No destinations loaded yet. Run the seed script.")
            try:
                _engine = RecommendationEngine(features, weights=get_settings().recommendation_weights)
            except Exception:
                log.exception("Failed to build recommendation engine")
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Recommendation engine unavailable") from None
            log.info("Recommendation engine ready: %s", _engine.describe())
        return _engine


# Common trip origins that aren't destinations in the dataset (approximate city centres).
MAJOR_CITIES = {
    "chennai": (13.0827, 80.2707), "pune": (18.5204, 73.8567), "ahmedabad": (23.0225, 72.5714),
    "lucknow": (26.8467, 80.9462), "patna": (25.5941, 85.1376), "bhopal": (23.2599, 77.4126),
    "chandigarh": (30.7333, 76.7794), "guwahati": (26.1445, 91.7362), "kanpur": (26.4499, 80.3319),
    "nagpur": (21.1458, 79.0882), "indore": (22.7196, 75.8577), "surat": (21.1702, 72.8311),
    "visakhapatnam": (17.6868, 83.2185), "coimbatore": (11.0168, 76.9558), "ranchi": (23.3441, 85.3096),
    "thiruvananthapuram": (8.5241, 76.9366), "raipur": (21.2514, 81.6296), "dehradun": (30.3165, 78.0322),
    "jammu": (32.7266, 74.8570), "cuttack": (20.4625, 85.8830), "vadodara": (22.3072, 73.1812),
    "noida": (28.5355, 77.3910), "gurugram": (28.4595, 77.0266), "kozhikode": (11.2588, 75.7804),
    "mangaluru": (12.9141, 74.8560), "madurai": (9.9252, 78.1198), "siliguri": (26.7271, 88.3953),
}


def resolve_origin(db: Session, text: str | None) -> tuple[str, tuple[float, float]] | None:
    """Match a free-text starting location against known cities (no geocoding API needed)."""
    if not text or not text.strip():
        return None
    q = text.strip().lower()
    for d in db.scalars(select(Destination)):
        name = d.name.lower()
        if name == q or name in q or (len(q) >= 4 and q in name):
            return d.name, (d.latitude, d.longitude)
    for city, coords in MAJOR_CITIES.items():
        if city in q:
            return city.title(), coords
    d = db.scalar(select(Destination).where(func.lower(Destination.state) == q))
    return (d.state, (d.latitude, d.longitude)) if d else None


def to_preferences(db: Session, req: RecommendationRequest) -> tuple[Preferences, str | None]:
    origin = resolve_origin(db, req.starting_location)
    note = None
    if req.starting_location and origin is None:
        note = f"Couldn't locate '{req.starting_location}', so travel to the destination is not included in costs."
    prefs = Preferences(
        budget=req.budget,
        duration=req.duration,
        travelers=req.travelers,
        destination_types=req.all_destination_types,
        interests=list(req.interests),
        travel_month=req.travel_date.month if req.travel_date else None,
        hotel_preference=req.hotel_preference,
        transport=req.transport_preference,
        notes=req.notes,
        origin_name=origin[0] if origin else None,
        origin=origin[1] if origin else None,
    )
    return prefs, note


def recommend(db: Session, req: RecommendationRequest) -> dict:
    engine = get_engine(db)
    prefs, note = to_preferences(db, req)
    return {
        "recommendations": engine.rank_destinations(prefs, top_k=req.top_k),
        "engine": engine.describe(),
        "query": engine.query_text(prefs),
        "notes": [note] if note else [],
    }
