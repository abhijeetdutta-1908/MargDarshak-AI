from typing import get_args

from app.schemas.preferences import DestinationType
from seed import generate_hotels, km, load_destinations, load_places


def test_destinations_are_valid():
    dests = load_destinations()
    assert len(dests) >= 30
    assert len({d["name"] for d in dests}) == len(dests)
    for d in dests:
        assert d["category"] in get_args(DestinationType), d["name"]
        assert 6 <= d["latitude"] <= 36 and 68 <= d["longitude"] <= 98, d["name"]  # inside India
        assert d["best_seasons"] and all(1 <= m <= 12 for m in d["best_seasons"]), d["name"]
        assert 1 <= d["ideal_min_days"] <= d["ideal_max_days"], d["name"]
        assert 0 <= d["popularity_score"] <= 1, d["name"]
        assert len(d["tags"]) >= 4 and len(d["description"]) > 80, d["name"]
        # daily per-person spend must cover at least a half-share of a room plus food and transport
        floor = d["average_hotel_cost"] / 2 + d["average_food_cost"] + d["average_transport_cost"]
        assert d["average_daily_cost"] >= floor, d["name"]


def test_places_are_valid_and_near_their_destination():
    dests = {d["name"]: d for d in load_destinations()}
    places = load_places()
    kinds = [p["kind"] for p in places]
    assert kinds.count("attraction") >= 100
    assert kinds.count("restaurant") >= 50
    assert set(kinds) <= {"attraction", "restaurant", "shopping", "activity"}
    seen = set()
    for p in places:
        d = dests[p["destination"]]
        key = (p["destination"], p["name"])
        assert key not in seen, key
        seen.add(key)
        assert km(d["latitude"], d["longitude"], p["latitude"], p["longitude"]) < 160, key
        assert 1 <= p["rating"] <= 5 and p["estimated_cost"] >= 0 and p["duration_minutes"] > 0, key
    for name in dests:
        assert any(p["destination"] == name and p["kind"] == "attraction" for p in places), name
        assert any(p["destination"] == name and p["kind"] == "restaurant" for p in places), name


def test_generated_hotels_are_deterministic_and_tiered():
    d = load_destinations()[0]
    far = [("Far Away Peak", d["latitude"] + 1, d["longitude"])]
    a = generate_hotels(d, far)
    assert a == generate_hotels(d, far)
    assert all(h["address"] == f"Central {d['name']}" for h in a)  # never "near" a landmark ~110 km off
    assert len({h["name"] for h in a}) == len(a)
    by_tier = {h["tier"]: h["price_per_night"] for h in a}
    assert by_tier["budget"] < by_tier["premium"] < by_tier["luxury"]
    for h in a:
        assert km(d["latitude"], d["longitude"], h["latitude"], h["longitude"]) < 4
