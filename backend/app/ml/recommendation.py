"""Hybrid destination recommender.

Pipeline:  preferences -> query text -> embedding -> FAISS top-k  (+ category matches)
           -> budget pre-filter -> weighted content-based score -> reasons -> ranking

Every component score is in [0, 1]; the final score is their weighted sum scaled to 0-100.
"""

import math
from dataclasses import dataclass, field

import numpy as np

from app.ml.budget import BudgetCalculator, CostProfile
from app.ml.semantic import Embedder, VectorIndex, destination_text, fingerprint, load_artifacts
from app.ml.vocab import TYPE_TAGS, interest_matches

DEFAULT_WEIGHTS = {
    "interest": 0.20,  # keyword overlap of interests with destination tags
    "semantic": 0.10,  # embedding similarity of the whole preference text
    "type": 0.15,  # destination type (beach, mountain, ...)
    "budget": 0.20,
    "duration": 0.10,
    "season": 0.10,
    "activity": 0.05,  # interests supported by actual places there
    "hotel": 0.05,  # preferred hotel tier available within budget
    "popularity": 0.05,
}
# Off-season can mean closed passes or monsoon; a 10% weight alone can't outweigh a perfect type match.
OFF_SEASON_PENALTY = 0.8
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


@dataclass
class Preferences:
    budget: int
    duration: int
    travelers: int = 1
    destination_types: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    travel_month: int | None = None
    hotel_preference: str | None = None
    transport: str | None = None
    notes: str | None = None
    origin_name: str | None = None
    origin: tuple[float, float] | None = None  # lat, lng


@dataclass
class DestinationFeatures:
    id: int
    name: str
    state: str
    category: str
    description: str
    tags: list[str]
    best_seasons: list[int]
    ideal_min_days: int
    ideal_max_days: int
    average_daily_cost: int
    average_hotel_cost: int
    average_food_cost: int
    average_transport_cost: int
    popularity_score: float
    latitude: float
    longitude: float
    place_tags: list[set[str]] = field(default_factory=list)
    hotel_prices: dict[str, list[int]] = field(default_factory=dict)

    @property
    def tag_set(self) -> set[str]:
        return set(self.tags) | {self.category}

    def cost_profile(self) -> CostProfile:
        return CostProfile(self.name, self.average_daily_cost, self.average_hotel_cost, self.average_food_cost,
                           self.average_transport_cost, self.hotel_prices)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def _inr(v: float) -> str:
    return f"₹{round(v):,}"


class RecommendationEngine:
    def __init__(self, destinations: list[DestinationFeatures], embedder: Embedder | None = None,
                 weights: dict[str, float] | None = None):
        if not destinations:
            raise ValueError("RecommendationEngine needs at least one destination")
        self.destinations = destinations
        w = {**DEFAULT_WEIGHTS, **(weights or {})}
        total = sum(w.values())
        self.weights = {k: v / total for k, v in w.items()}

        texts = [destination_text(d.name, d.category, d.tags, d.description) for d in destinations]
        self.embedder = (embedder or Embedder()).fit(texts)
        fp = fingerprint(texts, self.embedder.backend)
        cached = load_artifacts(fp)
        if cached is not None:
            vectors, faiss_index = cached
            self.artifacts = "prebuilt"
        else:
            vectors, faiss_index = self.embedder.encode(texts), None
            self.artifacts = "built-at-startup"
        self.index = VectorIndex(vectors, faiss_index)

    # ---- metadata ------------------------------------------------------------------------
    def describe(self) -> dict:
        return {"embedding": self.embedder.backend, "index": self.index.backend, "vectors": self.artifacts,
                "weights": {k: round(v, 3) for k, v in self.weights.items()}}

    @staticmethod
    def query_text(p: Preferences) -> str:
        parts = []
        if p.destination_types:
            parts.append(f"I want a {' or '.join(p.destination_types)} destination.")
        if p.interests:
            parts.append(f"I enjoy {', '.join(p.interests)}.")
        if p.notes:
            parts.append(p.notes)
        return " ".join(parts) or "A popular destination in India."

    # ---- retrieval -----------------------------------------------------------------------
    def get_candidates(self, p: Preferences, k: int) -> list[tuple[DestinationFeatures, float]]:
        """FAISS top-k by semantic similarity, plus every destination of a requested type."""
        q = self.embedder.encode([self.query_text(p)])[0]
        hits = self.index.search(q, len(self.destinations))  # n is small; normalise over all
        sims = np.array([s for _, s in hits])
        lo, hi = float(sims.min()), float(sims.max())
        norm = {i: (s - lo) / (hi - lo) if hi > lo else 0.5 for i, s in hits}
        chosen = {i for i, _ in hits[:k]}
        chosen |= {i for i, d in enumerate(self.destinations) if d.category in p.destination_types}
        return [(self.destinations[i], norm[i]) for i in sorted(chosen, key=lambda i: -norm[i])]

    # ---- component scores (each 0..1) -----------------------------------------------------
    def calculate_type_score(self, p: Preferences, d: DestinationFeatures) -> tuple[float, str | None]:
        if not p.destination_types:
            return 1.0, None
        if d.category in p.destination_types:
            return 1.0, d.category
        for t in p.destination_types:
            if TYPE_TAGS.get(t, {t}) & d.tag_set:
                return 0.6, t
        return 0.0, None

    def calculate_interest_similarity(self, p: Preferences, d: DestinationFeatures) -> tuple[float, list[str]]:
        if not p.interests:
            return 1.0, []
        matched = [i for i in p.interests if interest_matches(i, d.tag_set)]
        return len(matched) / len(p.interests), matched

    def calculate_semantic_similarity(self, semantic_norm: float) -> float:
        return semantic_norm

    def estimate_cost(self, p: Preferences, d: DestinationFeatures) -> dict:
        km = haversine_km(p.origin, (d.latitude, d.longitude)) * 1.25 if p.origin else None  # road factor
        return BudgetCalculator(d.cost_profile(), p.duration, p.travelers, p.hotel_preference, p.transport,
                                intercity_km=km, origin=p.origin_name).calculate_total()

    def calculate_budget_score(self, p: Preferences, estimate: dict) -> float:
        ratio = estimate["average"] / max(p.budget, 1)
        return 1.0 if ratio <= 1 else max(0.0, 1 - (ratio - 1) / 0.6)

    def calculate_duration_score(self, p: Preferences, d: DestinationFeatures) -> float:
        if d.ideal_min_days <= p.duration <= d.ideal_max_days:
            return 1.0
        if p.duration < d.ideal_min_days:
            return max(0.0, 1 - (d.ideal_min_days - p.duration) / d.ideal_min_days)
        return max(0.3, 1 - (p.duration - d.ideal_max_days) / (d.ideal_max_days * 1.5))

    def calculate_season_score(self, p: Preferences, d: DestinationFeatures) -> float:
        if p.travel_month is None:
            return 1.0
        if p.travel_month in d.best_seasons:
            return 1.0
        adjacent = {(p.travel_month % 12) + 1, ((p.travel_month - 2) % 12) + 1}
        return 0.5 if adjacent & set(d.best_seasons) else 0.0

    def calculate_activity_score(self, p: Preferences, d: DestinationFeatures) -> tuple[float, list[str]]:
        if not p.interests or not d.place_tags:
            return (1.0 if not p.interests else 0.0), []
        supported = [i for i in p.interests if any(interest_matches(i, tags) for tags in d.place_tags)]
        return len(supported) / len(p.interests), supported

    def calculate_hotel_score(self, p: Preferences, d: DestinationFeatures) -> float:
        if not p.hotel_preference:
            return 1.0
        prices = d.hotel_prices.get(p.hotel_preference)
        if not prices:
            return 0.2
        rooms = math.ceil(p.travelers / 2)
        affordable_nightly = p.budget * 0.45 / max(1, p.duration - 1) / rooms  # ~45% of budget on rooms
        return 1.0 if min(prices) <= affordable_nightly else 0.5

    def calculate_final_score(self, components: dict[str, float]) -> float:
        score = 100 * sum(self.weights[k] * components[k] for k in self.weights)
        if components["season"] == 0:
            score *= OFF_SEASON_PENALTY
        return round(score, 1)

    # ---- explanations ----------------------------------------------------------------------
    def generate_reasons(self, p: Preferences, d: DestinationFeatures, c: dict[str, float], ctx: dict) -> tuple[list[str], list[str]]:
        reasons, warnings = [], []
        if ctx["type_hit"]:
            strength = "Strong match" if c["type"] == 1 else "Partial match"
            reasons.append(f"{strength} for your {ctx['type_hit']} preference")
        elif p.destination_types:
            warnings.append(f"Not a {' / '.join(p.destination_types)} destination")
        if ctx["interests"]:
            reasons.append(f"Suitable for {', '.join(ctx['interests'])}")
        missing = [i for i in p.interests if i not in ctx["interests"]]
        if missing and p.interests:
            warnings.append(f"Limited options for {', '.join(missing)}")
        est = ctx["estimate"]["average"]
        if c["budget"] == 1:
            reasons.append(f"Fits your budget (est. {_inr(est)} of {_inr(p.budget)})")
        else:
            warnings.append(f"Likely over budget by ~{_inr(est - p.budget)} (est. {_inr(est)})")
        if c["duration"] == 1:
            reasons.append(f"Good match for a {p.duration}-day trip (ideal {d.ideal_min_days}–{d.ideal_max_days} days)")
        elif p.duration < d.ideal_min_days:
            warnings.append(f"Best enjoyed over {d.ideal_min_days}+ days")
        else:
            warnings.append(f"{p.duration} days is longer than needed (ideal {d.ideal_min_days}–{d.ideal_max_days})")
        if p.travel_month:
            month = MONTHS[p.travel_month - 1]
            if c["season"] == 1:
                reasons.append(f"{month} is one of the best months to visit")
            elif c["season"] == 0.5:
                warnings.append(f"{month} is at the edge of the best season")
            else:
                warnings.append(f"{month} is off-season here (score reduced by {round((1 - OFF_SEASON_PENALTY) * 100)}%)")
        if p.hotel_preference:
            if c["hotel"] == 1:
                reasons.append(f"{p.hotel_preference.capitalize()} hotels available within budget")
            elif c["hotel"] == 0.5:
                warnings.append(f"{p.hotel_preference.capitalize()} hotels may stretch the budget")
        if ctx["semantic"] >= 0.75 and (p.notes or p.interests):
            reasons.append("Description closely matches what you're looking for")
        if d.popularity_score >= 0.85:
            reasons.append("Highly popular with travellers")
        return reasons, warnings

    # ---- ranking -------------------------------------------------------------------------
    def rank_destinations(self, p: Preferences, top_k: int = 6) -> list[dict]:
        completeness = 0.5 + 0.1 * sum(bool(x) for x in (p.interests, p.destination_types, p.travel_month,
                                                          p.hotel_preference, p.notes or p.origin))
        candidates = self.get_candidates(p, k=max(top_k * 3, 15))
        scored = []
        for d, sem in candidates:
            estimate = self.estimate_cost(p, d)
            type_score, type_hit = self.calculate_type_score(p, d)
            interest_score, interests = self.calculate_interest_similarity(p, d)
            activity_score, _ = self.calculate_activity_score(p, d)
            components = {
                "interest": interest_score,
                "semantic": self.calculate_semantic_similarity(sem),
                "type": type_score,
                "budget": self.calculate_budget_score(p, estimate),
                "duration": self.calculate_duration_score(p, d),
                "season": self.calculate_season_score(p, d),
                "activity": activity_score,
                "hotel": self.calculate_hotel_score(p, d),
                "popularity": d.popularity_score,
            }
            score = self.calculate_final_score(components)
            reasons, warnings = self.generate_reasons(
                p, d, components, {"type_hit": type_hit, "interests": interests, "estimate": estimate, "semantic": sem}
            )
            scored.append({
                "destination_id": d.id,
                "destination": d.name,
                "state": d.state,
                "category": d.category,
                "score": score,
                "confidence": round(score / 100 * completeness, 2),
                "reasons": reasons,
                "warnings": warnings,
                "components": {k: round(v * 100, 1) for k, v in components.items()},
                "estimated_cost": {k: estimate[k] for k in ("minimum", "average", "maximum")},
                "best_seasons": d.best_seasons,
                "latitude": d.latitude,
                "longitude": d.longitude,
            })
        # Budget filter: drop destinations far over budget unless that would leave too few.
        within = [s for s in scored if s["components"]["budget"] > 0]
        pool = within if len(within) >= top_k else scored
        pool.sort(key=lambda s: (-s["score"], s["destination"]))
        return pool[:top_k]
