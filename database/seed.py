"""Seed the travel catalogue from ml/datasets/.

    python database/seed.py            # insert anything missing (safe to re-run; runs on container start)
    python database/seed.py --update   # also overwrite existing rows with dataset values

Destinations and places come from hand-authored CSVs. Hotels are *generated* sample listings
(deterministic per destination) — they are not real properties, prices or availability.
"""

import argparse
import csv
import math
import random
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
DATASETS = ROOT / "ml" / "datasets"

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

TIER_PRICE = {"budget": 0.4, "standard": 1.0, "premium": 2.0, "luxury": 4.0}
TIER_RATING = {"budget": (3.4, 4.1), "standard": (3.8, 4.4), "premium": (4.1, 4.6), "luxury": (4.4, 4.9)}
TIER_NAMES = {
    "budget": ["{c} Backpackers Hostel", "{c} Traveller's Nest", "Green Leaf Guesthouse {c}", "{c} Budget Inn"],
    "standard": ["Hotel {c} Comfort", "The {c} Courtyard Inn", "{c} Residency", "Silver Oak Hotel {c}", "{c} Park View Hotel"],
    "premium": ["The {c} Grand", "{c} Heritage Suites", "Royal Crest {c}"],
    "luxury": ["The {c} Palace Retreat", "{c} Luxury Resort & Spa", "Aurum Collection {c}"],
}
TIER_AMENITIES = {
    "budget": ["Free Wi-Fi", "Hot water", "24-hour front desk"],
    "standard": ["Free Wi-Fi", "Air conditioning", "Restaurant", "Room service", "24-hour front desk"],
    "premium": ["Free Wi-Fi", "Air conditioning", "Restaurant", "Room service", "Gym", "Breakfast included", "Airport transfer"],
    "luxury": ["Free Wi-Fi", "Air conditioning", "Fine dining", "Spa", "Swimming pool", "Gym", "Concierge", "Breakfast included", "Airport transfer"],
}
OPTIONAL_AMENITIES = ["Parking", "Mountain view", "Sea view", "Lake view", "Shared kitchen", "Laundry", "Pet friendly", "Bonfire"]
HOTEL_PLAN = ["budget", "standard", "standard", "premium", "luxury"]


def _list(v: str) -> list[str]:
    return [x.strip() for x in v.split("|") if x.strip()]


def load_destinations() -> list[dict]:
    with open(DATASETS / "destinations.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["tags"] = _list(r["tags"])
        r["best_seasons"] = [int(m) for m in _list(r["best_seasons"])]
        for k in ("ideal_min_days", "ideal_max_days", "average_daily_cost", "average_hotel_cost",
                  "average_food_cost", "average_transport_cost"):
            r[k] = int(r[k])
        for k in ("popularity_score", "latitude", "longitude"):
            r[k] = float(r[k])
        r["country"] = "India"
    return rows


def load_places() -> list[dict]:
    with open(DATASETS / "places.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["tags"] = _list(r["tags"])
        r["is_indoor"] = r["is_indoor"] == "1"
        r["rating"] = float(r["rating"])
        r["estimated_cost"] = int(r["estimated_cost"])
        r["duration_minutes"] = int(r["duration_minutes"])
        r["latitude"] = float(r["latitude"])
        r["longitude"] = float(r["longitude"])
    return rows


def km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b_lng - a_lng) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def _address(city: str, lat: float, lng: float, landmarks: list[tuple[str, float, float]]) -> str:
    near = min(landmarks, key=lambda l: km(lat, lng, l[1], l[2]), default=None)
    if near and km(lat, lng, near[1], near[2]) <= 3:
        return f"Near {near[0]}, {city}"
    return f"Central {city}"


def generate_hotels(dest: dict, landmarks: list[tuple[str, float, float]]) -> list[dict]:
    """Deterministic sample hotels around the destination centre (within ~2.5 km)."""
    rng = random.Random(zlib.crc32(dest["name"].encode()))
    city = dest["name"]
    names = {tier: rng.sample(pool, k=HOTEL_PLAN.count(tier)) for tier, pool in TIER_NAMES.items()}
    hotels = []
    for tier in HOTEL_PLAN:
        lo, hi = TIER_RATING[tier]
        price = dest["average_hotel_cost"] * TIER_PRICE[tier] * rng.uniform(0.85, 1.15)
        lat = dest["latitude"] + rng.uniform(-0.02, 0.02)
        lng = dest["longitude"] + rng.uniform(-0.02, 0.02) / math.cos(math.radians(dest["latitude"]))
        hotels.append({
            "name": names[tier].pop().format(c=city),
            "tier": tier,
            "rating": round(rng.uniform(lo, hi), 1),
            "price_per_night": int(round(price / 50) * 50),
            "address": _address(city, lat, lng, landmarks),
            "amenities": TIER_AMENITIES[tier] + rng.sample(OPTIONAL_AMENITIES, k=2),
            "latitude": round(lat, 5),
            "longitude": round(lng, 5),
        })
    return hotels


def _upsert(db: Session, model, existing, values: dict, update: bool) -> int:
    """Returns 1 if a row was inserted or updated."""
    if existing is None:
        db.add(model(**values))
        return 1
    if update:
        for k, v in values.items():
            setattr(existing, k, v)
        return 1
    return 0


def seed(db: Session, update: bool = False) -> dict[str, int]:
    from app.models import Destination, Hotel, Place

    counts = {"destinations": 0, "places": 0, "hotels": 0}
    by_name = {d.name: d for d in db.scalars(select(Destination))}
    for row in load_destinations():
        counts["destinations"] += _upsert(db, Destination, by_name.get(row["name"]), row, update)
    db.flush()
    by_name = {d.name: d for d in db.scalars(select(Destination))}

    places = load_places()
    existing_places = {(p.destination_id, p.name): p for p in db.scalars(select(Place))}
    for row in places:
        dest = by_name[row.pop("destination")]
        values = {**row, "destination_id": dest.id}
        counts["places"] += _upsert(db, Place, existing_places.get((dest.id, row["name"])), values, update)

    existing_hotels = {(h.destination_id, h.name): h for h in db.scalars(select(Hotel))}
    landmarks = {}
    for p in load_places():
        if p["kind"] == "attraction":
            landmarks.setdefault(p["destination"], []).append((p["name"], p["latitude"], p["longitude"]))
    for name, dest in by_name.items():
        for h in generate_hotels({"name": name, "latitude": dest.latitude, "longitude": dest.longitude,
                                  "average_hotel_cost": dest.average_hotel_cost}, landmarks.get(name, [])):
            values = {**h, "destination_id": dest.id}
            counts["hotels"] += _upsert(db, Hotel, existing_hotels.get((dest.id, h["name"])), values, update)

    db.commit()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update", action="store_true", help="overwrite existing rows with dataset values")
    args = parser.parse_args()

    from app.database import SessionLocal

    with SessionLocal() as db:
        counts = seed(db, update=args.update)
    verb = "inserted/updated" if args.update else "inserted"
    print("Seed complete — " + ", ".join(f"{v} {k} {verb}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
