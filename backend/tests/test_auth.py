from app.models import User


def test_register_hashes_password_and_normalises_email(client, db, auth_headers):
    user = db.query(User).one()
    assert user.email == "asha@example.com"
    assert user.password_hash != "trip2026!" and user.password_hash.startswith("$2")


def test_duplicate_email_rejected(client, auth_headers):
    r = client.post("/api/auth/register", json={"name": "Other", "email": "asha@example.com", "password": "trip2026!"})
    assert r.status_code == 409


def test_weak_password_rejected(client):
    r = client.post("/api/auth/register", json={"name": "Weak", "email": "w@example.com", "password": "password"})
    assert r.status_code == 422


def test_login_and_me(client, auth_headers):
    bad = client.post("/api/auth/login", json={"email": "asha@example.com", "password": "wrong-pass1"})
    assert bad.status_code == 401
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "trip2026!"})
    assert unknown.status_code == 401 and unknown.json() == bad.json()

    r = client.post("/api/auth/login", json={"email": "ASHA@example.com", "password": "trip2026!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["name"] == "Asha"
    assert "password_hash" not in me.json()


def test_protected_routes_reject_missing_or_bad_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_logout_revokes_token(client, auth_headers):
    assert client.post("/api/auth/logout", headers=auth_headers).status_code == 204
    assert client.get("/api/auth/me", headers=auth_headers).status_code == 401
