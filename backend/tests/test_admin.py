import pytest

from app.models import User
from seed import ensure_admin, seed

DEST = {"name": "Testville", "state": "Odisha", "description": "A quiet test town with temples, lakes and good food.",
        "latitude": 20.1, "longitude": 85.5, "category": "nature", "tags": ["Lakes", "temples"], "best_seasons": [10, 11],
        "ideal_min_days": 1, "ideal_max_days": 3, "average_daily_cost": 2000, "average_hotel_cost": 1500,
        "average_food_cost": 400, "average_transport_cost": 300}


@pytest.fixture
def admin(client, db, auth_headers):
    seed(db)
    db.query(User).filter_by(email="asha@example.com").update({"is_admin": True})
    db.commit()
    return auth_headers


def test_admin_routes_require_admin(client, db, auth_headers):
    assert client.get("/api/admin/stats").status_code == 401
    assert client.get("/api/admin/stats", headers=auth_headers).status_code == 403
    assert client.post("/api/admin/destinations", json=DEST, headers=auth_headers).status_code == 403


def test_destination_and_hotel_crud(client, admin):
    r = client.post("/api/admin/destinations", json=DEST, headers=admin)
    assert r.status_code == 201 and r.json()["tags"] == ["lakes", "temples"]
    did = r.json()["id"]
    assert client.post("/api/admin/destinations", json=DEST, headers=admin).status_code == 409
    bad = client.post("/api/admin/destinations", json={**DEST, "name": "X2", "ideal_min_days": 5}, headers=admin)
    assert bad.status_code == 422
    # the new destination is immediately recommendable (engine cache invalidated)
    recs = client.post("/api/recommendations", json={"budget": 50000, "duration": 2, "notes": "Testville", "top_k": 20}).json()
    assert "Testville" in [x["destination"] for x in recs["recommendations"]]

    upd = client.put(f"/api/admin/destinations/{did}", json={**DEST, "popularity_score": 0.9}, headers=admin)
    assert upd.json()["popularity_score"] == 0.9

    hotel = {"destination_id": did, "name": "Lake Inn", "tier": "budget", "rating": 4.1, "price_per_night": 900,
             "address": "Lake Road", "amenities": ["Wi-Fi"], "latitude": 20.1, "longitude": 85.5}
    h = client.post("/api/admin/hotels", json=hotel, headers=admin).json()
    assert client.get("/api/admin/hotels", params={"destination_id": did}, headers=admin).json()[0]["name"] == "Lake Inn"
    changed = client.put(f"/api/admin/hotels/{h['id']}", json={**hotel, "price_per_night": 1100}, headers=admin)
    assert changed.json()["price_per_night"] == 1100
    assert client.delete(f"/api/admin/hotels/{h['id']}", headers=admin).status_code == 204
    assert client.delete(f"/api/admin/destinations/{did}", headers=admin).status_code == 204
    assert client.get(f"/api/destinations/{did}").status_code == 404


def test_cannot_delete_destination_with_trips(client, admin):
    from datetime import date, timedelta

    goa = client.get("/api/destinations/search", params={"q": "Goa"}).json()["items"][0]["id"]
    body = {"budget": 40000, "duration": 2, "destination_id": goa,
            "travel_date": (date.today() + timedelta(days=20)).isoformat()}
    assert client.post("/api/trips/generate", json=body, headers=admin).status_code == 201
    assert client.delete(f"/api/admin/destinations/{goa}", headers=admin).status_code == 409


def test_users_and_moderation(client, admin):
    dest = client.get("/api/destinations/search", params={"q": "Goa"}).json()["items"][0]["id"]
    r = client.post("/api/auth/register", json={"name": "Troll", "email": "troll@example.com", "password": "trip2026!"})
    troll = {"Authorization": f"Bearer {r.json()['access_token']}"}
    rev = client.post(f"/api/destinations/{dest}/reviews", json={"rating": 1, "comment": "spam spam spam"}, headers=troll).json()

    users = client.get("/api/admin/users", params={"q": "troll"}, headers=admin).json()
    assert users["total"] == 1 and users["items"][0]["review_count"] == 1
    me = client.get("/api/auth/me", headers=admin).json()
    assert client.put(f"/api/admin/users/{me['id']}", json={"is_admin": False}, headers=admin).status_code == 400

    assert client.put(f"/api/admin/reviews/{rev['id']}", json={"is_hidden": True}, headers=admin).json()["is_hidden"]
    assert client.get(f"/api/destinations/{dest}/reviews").json()["review_count"] == 0
    assert client.get("/api/admin/reviews", params={"hidden": True}, headers=admin).json()["total"] == 1
    assert client.get("/api/admin/stats", headers=admin).json()["hidden_reviews"] == 1
    assert client.delete(f"/api/admin/reviews/{rev['id']}", headers=admin).status_code == 204


def test_admin_bootstrap(db):
    assert "register it first" in ensure_admin(db, "new@example.com")
    assert "granted" in ensure_admin(db, "New@Example.com", "admin-pass-1")
    assert db.query(User).filter_by(email="new@example.com").one().is_admin
