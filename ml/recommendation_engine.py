"""Run the hybrid recommender from the command line, straight from the CSV datasets (no DB, no API).

    python ml/recommendation_engine.py --budget 20000 --days 4 --travelers 2 --type mountain \
        --interests trekking nature photography --month 11 --hotel budget
    python ml/recommendation_engine.py --notes "quiet beaches and coral reefs" --budget 60000 --days 5

The engine itself lives in backend/app/ml/recommendation.py so the API and this script share one implementation.
"""

import argparse
from collections import defaultdict

from _common import ROOT  # noqa: F401  (sets sys.path)
from seed import generate_hotels, load_destinations, load_places

from app.ml.recommendation import DestinationFeatures, Preferences, RecommendationEngine


def features_from_csv() -> list[DestinationFeatures]:
    places = load_places()
    tags, landmarks = defaultdict(list), defaultdict(list)
    for p in places:
        tags[p["destination"]].append(set(p["tags"]) | {p["kind"]})
        if p["kind"] == "attraction":
            landmarks[p["destination"]].append((p["name"], p["latitude"], p["longitude"]))
    out = []
    for i, d in enumerate(load_destinations(), start=1):
        prices = defaultdict(list)
        for h in generate_hotels(d, landmarks[d["name"]]):
            prices[h["tier"]].append(h["price_per_night"])
        fields = {k: d[k] for k in DestinationFeatures.__dataclass_fields__ if k in d}
        out.append(DestinationFeatures(id=i, **fields, place_tags=tags[d["name"]], hotel_prices=dict(prices)))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--budget", type=int, default=20000)
    ap.add_argument("--days", type=int, default=4)
    ap.add_argument("--travelers", type=int, default=2)
    ap.add_argument("--type", nargs="*", default=[], dest="types")
    ap.add_argument("--interests", nargs="*", default=[])
    ap.add_argument("--month", type=int)
    ap.add_argument("--hotel", choices=["budget", "standard", "premium", "luxury"])
    ap.add_argument("--notes")
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()

    engine = RecommendationEngine(features_from_csv())
    prefs = Preferences(budget=a.budget, duration=a.days, travelers=a.travelers, destination_types=a.types,
                        interests=a.interests, travel_month=a.month, hotel_preference=a.hotel, notes=a.notes)
    print(f"Engine: {engine.describe()}\nQuery:  {engine.query_text(prefs)}\n")
    for rank, r in enumerate(engine.rank_destinations(prefs, a.top), start=1):
        print(f"{rank}. {r['destination']} ({r['state']}) — {r['score']}/100, confidence {r['confidence']}")
        for reason in r["reasons"]:
            print(f"     ✓ {reason}")
        for warning in r["warnings"]:
            print(f"     ! {warning}")
        cost = r["estimated_cost"]
        print(f"     est. ₹{cost['minimum']:,} – ₹{cost['maximum']:,} (avg ₹{cost['average']:,})\n")


if __name__ == "__main__":
    main()
