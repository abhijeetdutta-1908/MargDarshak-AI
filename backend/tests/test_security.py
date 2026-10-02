import pytest

from app.config import get_settings
from app.main import app
from app.utils import ratelimit


@pytest.fixture
def limits_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    for limiter in ratelimit.ALL:
        limiter.reset()
    yield
    for limiter in ratelimit.ALL:
        limiter.reset()


def test_login_is_rate_limited(client, limits_on):
    body = {"email": "nobody@example.com", "password": "wrong-pass1"}
    codes = [client.post("/api/auth/login", json=body).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10 and codes[10] == 429
    r = client.post("/api/auth/login", json=body)
    assert int(r.headers["Retry-After"]) > 0 and "Too many requests" in r.json()["detail"]


def test_limits_are_per_client_ip(client, limits_on):
    body = {"email": "x@example.com", "password": "wrong-pass1"}
    for _ in range(10):
        client.post("/api/auth/login", json=body, headers={"X-Real-IP": "10.0.0.1"})
    assert client.post("/api/auth/login", json=body, headers={"X-Real-IP": "10.0.0.1"}).status_code == 429
    assert client.post("/api/auth/login", json=body, headers={"X-Real-IP": "10.0.0.2"}).status_code == 401


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Cache-Control"] == "no-store"


def test_unhandled_errors_do_not_leak_details(client):
    @app.get("/api/__boom")
    def boom():
        raise RuntimeError("secret internal detail")

    try:
        r = TestClientNoRaise(client).get("/api/__boom")
        assert r.status_code == 500
        assert "secret" not in r.text and "Traceback" not in r.text
    finally:
        app.router.routes = [rt for rt in app.router.routes if getattr(rt, "path", "") != "/api/__boom"]


def TestClientNoRaise(client):  # noqa: N802
    from fastapi.testclient import TestClient

    return TestClient(client.app, raise_server_exceptions=False)


def test_password_hash_never_returned(client, auth_headers):
    for path in ("/api/auth/me", "/api/users/me"):
        assert "password" not in client.get(path, headers=auth_headers).text


def test_sql_injection_in_search_is_inert(client, db):
    from seed import seed

    seed(db)
    r = client.get("/api/destinations/search", params={"q": "' OR 1=1; DROP TABLE users; --"})
    assert r.status_code == 200 and r.json()["total"] == 0
    assert client.get("/api/destinations").json()["total"] >= 30


def test_tampered_or_expired_tokens_rejected(client, auth_headers):
    import jwt

    token = auth_headers["Authorization"].split()[1]
    payload = jwt.decode(token, options={"verify_signature": False})
    forged = jwt.encode(payload, "attacker-secret-" + "y" * 32, algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    expired = jwt.encode({**payload, "exp": 1}, get_settings().jwt_secret, algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    none_alg = jwt.encode(payload, None, algorithm="none")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {none_alg}"}).status_code == 401
