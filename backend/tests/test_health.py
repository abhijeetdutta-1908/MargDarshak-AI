import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health_ok():
    r = TestClient(app).get("/api/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"
