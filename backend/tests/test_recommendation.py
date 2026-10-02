import os
from datetime import date

import pytest

from app.ml.budget import BudgetCalculator, CostProfile
from app.ml.recommendation import Preferences, RecommendationEngine
from app.services.recommendations import load_features
from seed import seed


@pytest.fixture
def features(db):
    seed(db)
    return load_features(db)


@pytest.fixture
def engine(features):
    return RecommendationEngine(features)


def names(results):
    return [r["destination"] for r in results]


def test_mountain_trekker_in_november(engine):
    p = Preferences(budget=20000, duration=4, travelers=2, destination_types=["mountain"],
                    interests=["trekking", "nature", "photography"], travel_month=11, hotel_preference="budget")
    res = engine.rank_destinations(p, top_k=5)
    assert res[0]["category"] == "mountain"
    assert {"Manali", "Darjeeling", "Gangtok"} & set(names(res[:3]))
    top = res[0]
    assert any("mountain preference" in r for r in top["reasons"])
    assert any("trekking" in r for r in top["reasons"])
    assert 0 <= top["score"] <= 100 and 0 <= top["confidence"] <= 1


def test_beach_party_in_december(engine):
    p = Preferences(budget=60000, duration=5, travelers=2, destination_types=["beach"],
                    interests=["nightlife", "food", "relaxation"], travel_month=12)
    assert "Goa" in names(engine.rank_destinations(p, top_k=3))


def test_wildlife_photographer(engine):
    p = Preferences(budget=40000, duration=3, travelers=2, destination_types=["wildlife"],
                    interests=["wildlife", "photography"], travel_month=2)
    assert engine.rank_destinations(p, top_k=1)[0]["destination"] in {"Ranthambore", "Jim Corbett", "Kaziranga"}


def test_pilgrimage(engine):
    p = Preferences(budget=15000, duration=2, travelers=2, destination_types=["religious"],
                    interests=["culture", "history"], travel_month=1)
    assert set(names(engine.rank_destinations(p, top_k=3))) <= {"Varanasi", "Amritsar", "Puri", "Bodh Gaya"}


def test_season_changes_ranking_and_warns(engine):
    base = dict(budget=80000, duration=7, travelers=2, destination_types=["adventure"], interests=["trekking", "adventure"])
    summer = engine.rank_destinations(Preferences(**base, travel_month=7), top_k=3)
    assert "Leh" in names(summer)
    winter = engine.rank_destinations(Preferences(**base, travel_month=1), top_k=20)
    assert winter[0]["destination"] != "Leh"
    leh = next(r for r in winter if r["destination"] == "Leh")
    assert any("off-season" in w for w in leh["warnings"])
    assert leh["score"] < next(r for r in summer if r["destination"] == "Leh")["score"]


def test_tight_budget_warns(engine):
    p = Preferences(budget=3000, duration=5, travelers=2)
    res = engine.rank_destinations(p, top_k=3)
    assert len(res) == 3  # falls back rather than returning nothing
    assert all(any("over budget" in w for w in r["warnings"]) for r in res)


def test_results_sorted_deterministic_and_explained(engine):
    p = Preferences(budget=30000, duration=3, travelers=1, interests=["history"])
    a, b = engine.rank_destinations(p, top_k=8), engine.rank_destinations(p, top_k=8)
    assert a == b
    assert [r["score"] for r in a] == sorted([r["score"] for r in a], reverse=True)
    assert all(r["reasons"] for r in a)
    assert set(a[0]["components"]) == set(engine.weights)


def test_weights_are_configurable_and_normalised(features):
    e = RecommendationEngine(features, weights={"popularity": 5.0})
    assert abs(sum(e.weights.values()) - 1) < 1e-9
    top = e.rank_destinations(Preferences(budget=10**6, duration=3), top_k=1)[0]
    assert top["destination"] == "Goa"  # most popular wins when popularity dominates


def test_engine_reports_backends(engine):
    info = engine.describe()
    assert info["embedding"] in ("tfidf",) or info["embedding"].startswith("sentence-transformers")
    assert info["index"] in ("faiss", "numpy")


@pytest.mark.skipif(not os.getenv("RUN_ST_TESTS"), reason="set RUN_ST_TESTS=1 to exercise Sentence Transformers")
def test_sentence_transformer_semantics(features, monkeypatch):
    from app.ml import semantic

    monkeypatch.delenv("DISABLE_SENTENCE_TRANSFORMERS", raising=False)
    semantic._load_transformer.cache_clear()
    e = RecommendationEngine(features)
    assert e.describe()["embedding"].startswith("sentence-transformers")
    p = Preferences(budget=10**6, duration=4, notes="snow-capped peaks, high mountain passes and motorbike road trips")
    top3 = {d.name for d, _ in e.get_candidates(p, k=36)[:3]}
    assert "Leh" in top3, top3
    beach = Preferences(budget=10**6, duration=4, notes="turquoise water, coral reefs and white sand")
    assert {d.name for d, _ in e.get_candidates(beach, k=36)[:3]} & {"Havelock Island", "Port Blair", "Goa"}
    semantic._load_transformer.cache_clear()


# ---- BudgetCalculator ---------------------------------------------------------------------
PROFILE = CostProfile("Testpur", average_daily_cost=3000, average_hotel_cost=2000, average_food_cost=600,
                      average_transport_cost=400, hotel_prices={"budget": [800, 1000]})


def test_budget_components_sum_and_ranges():
    b = BudgetCalculator(PROFILE, duration=4, travelers=3, hotel_tier="budget", transport="public").calculate_total()
    for k in ("minimum", "average", "maximum"):
        key = {"minimum": "min", "average": "average", "maximum": "max"}[k]
        assert b[k] == sum(c[key] for c in b["components"].values())
    assert b["minimum"] < b["average"] < b["maximum"]
    # 3 nights x 2 rooms at the budget-tier average of 900
    assert b["components"]["accommodation"]["average"] == 3 * 2 * 900
    assert b["components"]["food"]["average"] == round(600 * 0.8 * 3 * 4)
    assert any("not included" in a for a in b["assumptions"])


def test_budget_selected_hotel_and_itinerary_costs():
    b = BudgetCalculator(PROFILE, duration=2, travelers=2, hotel_price=1500, activity_cost_per_person=700).calculate_total()
    acc = b["components"]["accommodation"]
    assert acc["min"] == acc["average"] == acc["max"] == 1500
    assert b["components"]["activities"]["average"] == 1400


def test_budget_intercity_switches_to_flight_when_far():
    near = BudgetCalculator(PROFILE, 3, 2, transport="public", intercity_km=300).calculate_total()
    far = BudgetCalculator(PROFILE, 3, 2, transport="public", intercity_km=2000).calculate_total()
    assert any("train/bus" in a for a in near["assumptions"])
    assert any("flight" in a for a in far["assumptions"])
    assert far["components"]["transportation"]["average"] > near["components"]["transportation"]["average"]


# ---- API ----------------------------------------------------------------------------------
def test_recommendation_api(client, db):
    seed(db)
    from app.services.recommendations import invalidate_catalog

    invalidate_catalog()
    body = {"budget": 20000, "duration": 4, "destination_type": "mountain", "interests": ["trekking", "nature", "photography"],
            "travel_date": date(date.today().year + 1, 11, 10).isoformat(), "hotel_preference": "budget", "travelers": 2,
            "starting_location": "Delhi"}
    r = client.post("/api/recommendations", json=body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["recommendations"] and data["engine"]["index"] in ("faiss", "numpy")
    first = data["recommendations"][0]
    assert {"score", "confidence", "reasons", "warnings", "components", "estimated_cost"} <= set(first)
    assert data["notes"] == []

    past = {**body, "travel_date": "2020-01-01"}
    assert client.post("/api/recommendations", json=past).status_code == 422
    unknown = client.post("/api/recommendations", json={**body, "starting_location": "Atlantis"}).json()
    assert "Couldn't locate" in unknown["notes"][0]
    invalidate_catalog()
