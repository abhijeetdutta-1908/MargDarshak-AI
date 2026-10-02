from datetime import date, timedelta

import pytest

from app.services.recommendations import invalidate_catalog
from seed import seed

FUTURE = (date.today() + timedelta(days=40)).isoformat()


@pytest.fixture
def seeded(db):
    seed(db)
    invalidate_catalog()
    yield
    invalidate_catalog()


def gen(client, headers, **overrides):
    body = {"budget": 30000, "duration": 3, "travelers": 2, "destination_type": "historical",
            "interests": ["history", "photography"], "travel_date": FUTURE, "hotel_preference": "standard",
            "transport_preference": "taxi", "starting_location": "Delhi", **overrides}
    return client.post("/api/trips/generate", json=body, headers=headers)


def test_generate_requires_login(client, seeded):
    assert gen(client, {}).status_code == 401


def test_generate_full_trip(client, seeded, auth_headers):
    r = gen(client, auth_headers)
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["destination"]["category"] == "historical"
    assert t["hotel"] and t["hotel"]["destination_id"] == t["destination"]["id"]
    assert len(t["days"]) == 3 and t["days"][0]["date"] == FUTURE
    assert t["days"][0]["items"][0]["category"] == "arrival"
    b = t["budget"]
    assert b["minimum"] <= b["average"] <= b["maximum"] and b["requested"] == 30000
    assert set(b["components"]) == {"accommodation", "transportation", "food", "activities", "miscellaneous"}
    assert any("Delhi" in a for a in b["assumptions"]) or t["destination"]["name"] == "Delhi"
    assert t["weather"]["source"] == "fallback"  # no key in tests
    assert t["recommendations"] and t["route"]["total_distance_km"] > 0
    assert t["is_saved"] is False


def test_generate_for_chosen_destination_and_hotel(client, seeded, auth_headers):
    dest = client.get("/api/destinations/search", params={"q": "Udaipur"}).json()["items"][0]
    hotels = client.get(f"/api/hotels/{dest['id']}").json()["items"]
    lux = next(h for h in hotels if h["tier"] == "luxury")
    t = gen(client, auth_headers, destination_id=dest["id"], hotel_id=lux["id"]).json()
    assert t["destination"]["name"] == "Udaipur" and t["hotel"]["id"] == lux["id"]
    assert t["budget"]["components"]["accommodation"]["average"] == lux["price_per_night"] * 2  # 2 nights, 1 room
    other = client.get("/api/destinations/search", params={"q": "Goa"}).json()["items"][0]
    goa_hotel = client.get(f"/api/hotels/{other['id']}").json()["items"][0]
    assert gen(client, auth_headers, destination_id=dest["id"], hotel_id=goa_hotel["id"]).status_code == 422


def test_trip_crud_share_duplicate_complete(client, seeded, auth_headers):
    t = gen(client, auth_headers).json()
    tid = t["id"]
    assert client.get(f"/api/trips/{tid}/itinerary", headers=auth_headers).json()[0]["day_number"] == 1

    r = client.put(f"/api/trips/{tid}", json={"title": "Heritage weekend", "is_saved": True}, headers=auth_headers)
    assert r.json()["title"] == "Heritage weekend" and r.json()["is_saved"]
    new_start = (date.today() + timedelta(days=60)).isoformat()
    r = client.put(f"/api/trips/{tid}", json={"start_date": new_start}, headers=auth_headers).json()
    assert r["days"][0]["date"] == new_start

    saved = client.get("/api/trips", params={"saved": True}, headers=auth_headers).json()
    assert saved["total"] == 1 and saved["items"][0]["id"] == tid

    share = client.post(f"/api/trips/{tid}/share", headers=auth_headers).json()
    public = client.get(f"/api/shared/{share['share_token']}")
    assert public.status_code == 200 and public.json()["id"] == tid and "user_id" not in public.json()
    client.delete(f"/api/trips/{tid}/share", headers=auth_headers)
    assert client.get(f"/api/shared/{share['share_token']}").status_code == 404

    dup = client.post(f"/api/trips/{tid}/duplicate", headers=auth_headers).json()
    assert dup["id"] != tid and dup["title"].endswith("(copy)")
    assert [len(d["items"]) for d in dup["days"]] == [len(d["items"]) for d in r["days"]]

    done = client.post(f"/api/trips/{tid}/complete", headers=auth_headers).json()
    assert done["is_completed"]
    dash = client.get("/api/dashboard", headers=auth_headers).json()
    assert dash["stats"]["total_trips"] == 2 and dash["travel_history"][0]["trip_id"] == tid
    assert dash["favourite_destinations"][0]["id"] == t["destination"]["id"]

    assert client.delete(f"/api/trips/{dup['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/trips/{dup['id']}", headers=auth_headers).status_code == 404


def test_regenerate_changes_itinerary(client, seeded, auth_headers):
    t = gen(client, auth_headers, duration=4).json()
    r = client.post(f"/api/trips/{t['id']}/itinerary/regenerate", headers=auth_headers).json()
    assert r["variation"] == 1 and r["hotel"]["id"] == t["hotel"]["id"]
    flat = lambda trip: [i["title"] for d in trip["days"] for i in d["items"]]  # noqa: E731
    assert flat(r) != flat(t)


def test_other_users_cannot_see_trips(client, seeded, auth_headers):
    tid = gen(client, auth_headers).json()["id"]
    other = client.post("/api/auth/register", json={"name": "Eve", "email": "eve@example.com", "password": "trip2026!"})
    eve = {"Authorization": f"Bearer {other.json()['access_token']}"}
    for method, path in [("get", f"/api/trips/{tid}"), ("put", f"/api/trips/{tid}"), ("delete", f"/api/trips/{tid}"),
                         ("post", f"/api/trips/{tid}/share"), ("post", f"/api/trips/{tid}/itinerary/regenerate")]:
        kwargs = {"json": {"title": "mine"}} if method == "put" else {}
        assert getattr(client, method)(path, headers=eve, **kwargs).status_code == 404
    assert client.get("/api/trips", headers=eve).json()["total"] == 0


def test_ranked_hotels_endpoint(client, seeded):
    dest = client.get("/api/destinations/search", params={"q": "Manali"}).json()["items"][0]
    ranked = client.get(f"/api/hotels/{dest['id']}", params={"preferred_tier": "budget", "nightly_budget": 1500}).json()
    assert ranked["items"][0]["tier"] == "budget" and ranked["items"][0]["reasons"]
    scores = [h["score"] for h in ranked["items"]]
    assert scores == sorted(scores, reverse=True)
    h = client.get(f"/api/hotels/item/{ranked['items'][0]['id']}").json()
    assert h["destination_name"] == "Manali" and "not real" in h["note"]
