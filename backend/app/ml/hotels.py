"""Hotel ranking: budget fit, rating, tier preference and distance to the places you'll visit."""

from dataclasses import dataclass

from app.ml.recommendation import haversine_km

TIERS = ["budget", "standard", "premium", "luxury"]
WEIGHTS = {"budget": 0.35, "rating": 0.25, "tier": 0.20, "distance": 0.20}


@dataclass
class HotelCandidate:
    id: int
    name: str
    tier: str
    rating: float
    price_per_night: int
    latitude: float
    longitude: float


def rank_hotels(hotels: list[HotelCandidate], preferred_tier: str | None, max_nightly: float | None,
                attractions: list[tuple[float, float]] | None = None) -> list[dict]:
    """Return hotels sorted best-first with a 0-100 score and plain-language reasons."""
    centroid = None
    if attractions:
        centroid = (sum(a[0] for a in attractions) / len(attractions), sum(a[1] for a in attractions) / len(attractions))
    out = []
    for h in hotels:
        reasons = []
        if max_nightly:
            budget = 1.0 if h.price_per_night <= max_nightly else max(0.0, 1 - (h.price_per_night / max_nightly - 1) / 0.75)
            if budget == 1:
                reasons.append("Within your nightly budget")
        else:
            budget = 1.0
        rating = max(0.0, (h.rating - 3.0) / 2.0)
        if h.rating >= 4.4:
            reasons.append(f"Highly rated ({h.rating})")
        if preferred_tier:
            gap = abs(TIERS.index(h.tier) - TIERS.index(preferred_tier))
            tier = {0: 1.0, 1: 0.5}.get(gap, 0.0)
            if gap == 0:
                reasons.append(f"Matches your {preferred_tier} preference")
        else:
            tier = 1.0
        if centroid:
            km = haversine_km(centroid, (h.latitude, h.longitude))
            distance = max(0.0, 1 - km / 15)
            if km <= 3:
                reasons.append(f"{km:.1f} km from your planned sights")
        else:
            distance = 1.0
        parts = {"budget": budget, "rating": rating, "tier": tier, "distance": distance}
        score = round(100 * sum(WEIGHTS[k] * v for k, v in parts.items()), 1)
        out.append({"hotel": h, "score": score, "reasons": reasons})
    return sorted(out, key=lambda x: (-x["score"], x["hotel"].price_per_night))
