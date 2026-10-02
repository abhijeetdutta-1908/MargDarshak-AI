import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-" + "x" * 32)
# Fast, deterministic TF-IDF path by default; RUN_ST_TESTS=1 exercises the transformer model.
os.environ.setdefault("DISABLE_SENTENCE_TRANSFORMERS", "1")
os.environ.setdefault("ML_ARTIFACTS_DIR", os.path.join(os.path.dirname(__file__), ".no-artifacts"))
for key in ("OPENWEATHER_API_KEY", "GOOGLE_MAPS_API_KEY", "GOOGLE_PLACES_API_KEY"):
    os.environ[key] = ""  # tests must never call real external APIs

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401  register tables
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    r = client.post("/api/auth/register", json={"name": "Asha", "email": "Asha@Example.com", "password": "trip2026!"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
