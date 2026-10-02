from datetime import date

import pytest

from app.ml.itinerary import DayWeather, HotelStay, ItineraryGenerator, PlaceItem
from seed import load_destinations, load_places


def build(name, days=4, rain=(), interests=("history", "culture"), food=None, variation=0, start=date(2026, 11, 10)):
    d = next(x for x in load_destinations() if x["name"] == name)
    places = [PlaceItem(i, p["name"], p["kind"], set(p["tags"]), p["is_indoor"], p["rating"], p["estimated_cost"],
                        p["duration_minutes"], p["latitude"], p["longitude"], p["description"])
              for i, p in enumerate(load_places()) if p["destination"] == name]
    weather = [DayWeather(rain_likely=(i + 1) in rain, summary="Rain" if (i + 1) in rain else "Clear")
               for i in range(days)]
    gen = ItineraryGenerator(name, (d["latitude"], d["longitude"]), days, places,
                             HotelStay(1, "Test Hotel", d["latitude"], d["longitude"]), list(interests), 2, start,
                             weather, food, "mixed", variation)
    return gen.generate()


def minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


@pytest.mark.parametrize("name", ["Jaipur", "Manali", "Goa", "Delhi", "Leh", "Varanasi"])
def test_timeline_is_ordered_and_complete(name):
    out = build(name, days=4)
    assert [d["day_number"] for d in out["days"]] == [1, 2, 3, 4]
    assert out["days"][0]["items"][0]["category"] == "arrival"
    assert out["days"][-1]["items"][-1]["category"] == "departure"
    for day in out["days"]:
        times = [(minutes(i["start_time"]), minutes(i["end_time"])) for i in day["items"]]
        for (s1, e1), (s2, _) in zip(times, times[1:], strict=False):
            assert s1 <= e1 <= s2, (name, day["day_number"], day["items"])
        assert sum(i["category"] == "meal" and i["title"].startswith("Lunch") for i in day["items"]) == 1
    sights = [i["title"] for d in out["days"] for i in d["items"] if i["category"] in ("attraction", "activity", "shopping")]
    assert len(sights) == len(set(sights)) and sights  # no place visited twice


def test_dates_follow_start_date():
    out = build("Jaipur", days=3)
    assert [d["date"] for d in out["days"]] == ["2026-11-10", "2026-11-11", "2026-11-12"]


def test_rain_moves_indoor_places_to_rainy_day():
    dry = build("Delhi", days=4)
    wet = build("Delhi", days=4, rain=(2,))
    day2 = [i for i in wet["days"][1]["items"] if i["category"] in ("attraction", "activity")]
    indoor_names = {p["name"] for p in load_places() if p["destination"] == "Delhi" and p["is_indoor"]}
    assert day2 and all(i["title"] in indoor_names for i in day2)
    assert any("Rain is likely on day 2" in e for e in wet["explanations"])
    assert not any("Rain" in e for e in dry["explanations"])


def test_rain_with_no_indoor_options_is_explained_honestly():
    out = build("Manali", days=3, rain=(2,), interests=("trekking", "adventure"))
    assert any("few indoor sights" in e for e in out["explanations"])


def test_veg_preference_picks_veg_restaurants():
    out = build("Varanasi", days=2, food="veg")
    veg = {p["name"] for p in load_places() if p["destination"] == "Varanasi" and p["kind"] == "restaurant" and "veg" in p["tags"]}
    meals = [i["title"].split(" at ", 1)[1] for d in out["days"] for i in d["items"] if " at " in i["title"] and i["category"] == "meal"]
    assert meals and all(m in veg for m in meals)


def test_single_day_trip():
    out = build("Agra", days=1)
    items = out["days"][0]["items"]
    assert items[0]["category"] == "arrival" and items[-1]["category"] == "departure"
    assert any(i["title"] == "Taj Mahal" for i in items)


def test_full_day_excursion_gets_its_own_dry_day():
    out = build("Leh", days=5, interests=("adventure", "photography"))
    for day in out["days"]:
        long_ones = [i for i in day["items"] if i["duration_minutes"] >= 300]
        if long_ones:
            assert day["day_number"] not in (1, 5)
            assert not any(i["title"].startswith("Lunch") and i["category"] == "meal" for i in day["items"])


def test_regenerate_variation_changes_plan_but_stays_valid():
    a = build("Jaipur", days=3, variation=0)
    b = build("Jaipur", days=3, variation=3)
    titles = lambda o: [i["title"] for d in o["days"] for i in d["items"]]  # noqa: E731
    assert titles(a) != titles(b)
    assert build("Jaipur", days=3, variation=3) == b  # deterministic per variation


def test_costs_and_route_totals():
    out = build("Jaipur", days=3)
    assert out["activity_cost_per_person"] == sum(d["activity_cost"] for d in out["days"]) // 2
    assert out["route"]["total_distance_km"] > 0 and out["route"]["source"] == "estimate"


def test_time_of_day_rules():
    out = build("Varanasi", days=3, interests=("culture", "photography"))
    items = {i["title"]: i for d in out["days"] for i in d["items"]}
    assert minutes(items["Dashashwamedh Ghat Ganga Aarti"]["start_time"]) >= 17 * 60 + 30  # evening ceremony
    boat = items["Sunrise boat ride on the Ganges"]
    assert minutes(boat["start_time"]) < 7 * 60  # actually at sunrise
    boat_day = next(d for d in out["days"] if boat in d["items"])
    assert boat_day["day_number"] != 1  # never on arrival day
    after = boat_day["items"][boat_day["items"].index(boat) + 1]
    assert after["title"] == "Breakfast"
    assert out["unscheduled"] == []
