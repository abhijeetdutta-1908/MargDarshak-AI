def test_update_profile(client, auth_headers):
    r = client.put(
        "/api/users/me",
        headers=auth_headers,
        json={"name": "  Asha Rao ", "profile_image": "https://example.com/a.png"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Asha Rao"
    assert r.json()["profile_image"] == "https://example.com/a.png"


def test_update_email_conflict(client, auth_headers):
    client.post("/api/auth/register", json={"name": "Ravi", "email": "ravi@example.com", "password": "trip2026!"})
    r = client.put("/api/users/me", headers=auth_headers, json={"email": "ravi@example.com"})
    assert r.status_code == 409


def test_change_password(client, auth_headers):
    wrong = client.post(
        "/api/users/me/password", headers=auth_headers, json={"current_password": "nope", "new_password": "newpass99"}
    )
    assert wrong.status_code == 400

    r = client.post(
        "/api/users/me/password",
        headers=auth_headers,
        json={"current_password": "trip2026!", "new_password": "newpass99"},
    )
    assert r.status_code == 200
    # old token revoked, new one works, new password logs in
    assert client.get("/api/users/me", headers=auth_headers).status_code == 401
    new = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/api/users/me", headers=new).status_code == 200
    login = client.post("/api/auth/login", json={"email": "asha@example.com", "password": "newpass99"})
    assert login.status_code == 200


def test_preferences_roundtrip(client, auth_headers):
    empty = client.get("/api/preferences", headers=auth_headers)
    assert empty.status_code == 200 and empty.json()["interests"] == []

    body = {
        "destination_types": ["mountain", "nature"],
        "interests": ["trekking", "photography"],
        "budget_min": 10000,
        "budget_max": 25000,
        "hotel_preference": "budget",
        "transport_preference": "public",
        "food_preference": "veg",
        "travelers": 2,
        "starting_location": "Bhubaneswar",
    }
    r = client.put("/api/preferences", headers=auth_headers, json=body)
    assert r.status_code == 200 and r.json() == body
    assert client.get("/api/preferences", headers=auth_headers).json() == body


def test_preferences_validation(client, auth_headers):
    bad_type = client.put("/api/preferences", headers=auth_headers, json={"destination_types": ["moon"]})
    assert bad_type.status_code == 422
    bad_budget = client.put("/api/preferences", headers=auth_headers, json={"budget_min": 5000, "budget_max": 100})
    assert bad_budget.status_code == 422
