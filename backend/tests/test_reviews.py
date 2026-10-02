import pytest

from seed import seed


@pytest.fixture
def dest_id(client, db):
    seed(db)
    return client.get("/api/destinations/search", params={"q": "Hampi"}).json()["items"][0]["id"]


def other_user(client, email="ravi@example.com"):
    r = client.post("/api/auth/register", json={"name": "Ravi", "email": email, "password": "trip2026!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_review_lifecycle(client, dest_id, auth_headers):
    assert client.post(f"/api/destinations/{dest_id}/reviews", json={"rating": 5}).status_code == 401
    r = client.post(f"/api/destinations/{dest_id}/reviews", headers=auth_headers,
                    json={"rating": 5, "comment": "  Sunset from Matanga Hill was unforgettable.  "})
    assert r.status_code == 201 and r.json()["comment"].startswith("Sunset") and r.json()["user_name"] == "Asha"
    rid = r.json()["id"]
    dup = client.post(f"/api/destinations/{dest_id}/reviews", headers=auth_headers, json={"rating": 4})
    assert dup.status_code == 409

    ravi = other_user(client)
    client.post(f"/api/destinations/{dest_id}/reviews", headers=ravi, json={"rating": 2, "comment": "Too hot in May."})
    page = client.get(f"/api/destinations/{dest_id}/reviews").json()
    assert page["review_count"] == 2 and page["average_rating"] == 3.5 and page["distribution"]["5"] == 1
    detail = client.get(f"/api/destinations/{dest_id}").json()
    assert detail["average_rating"] == 3.5 and detail["review_count"] == 2

    assert client.put(f"/api/reviews/{rid}", headers=ravi, json={"rating": 1}).status_code == 403
    assert client.delete(f"/api/reviews/{rid}", headers=ravi).status_code == 403
    upd = client.put(f"/api/reviews/{rid}", headers=auth_headers, json={"rating": 4}).json()
    assert upd["rating"] == 4 and upd["comment"].startswith("Sunset")
    assert [x["id"] for x in client.get("/api/reviews/me", headers=auth_headers).json()] == [rid]
    assert any(x["id"] == rid for x in client.get("/api/reviews/recent").json())
    assert client.delete(f"/api/reviews/{rid}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/destinations/{dest_id}/reviews").json()["review_count"] == 1


def test_review_validation(client, dest_id, auth_headers):
    for bad in ({"rating": 0}, {"rating": 6}, {"rating": 3, "comment": "x" * 2001}):
        assert client.post(f"/api/destinations/{dest_id}/reviews", headers=auth_headers, json=bad).status_code == 422
    assert client.post("/api/destinations/9999/reviews", headers=auth_headers, json={"rating": 3}).status_code == 404
