import itertools
import json
import random
import time

import httpx
import pytest

from app.config import get_settings
from app.main import app
from app.ml.route import RouteOptimizer
from app.services import maps, places, weather
from app.services.http import get_http
from seed import seed


@pytest.fixture
def seeded(db):
    seed(db)


@pytest.fixture
def mock_http(client):
    """Route outbound calls to a handler: mock_http(lambda request: httpx.Response(...))."""
    calls = []

    def install(handler):
        def wrapped(request):
            calls.append(request)
            return handler(request)

        mock = httpx.AsyncClient(transport=httpx.MockTransport(wrapped))
        app.dependency_overrides[get_http] = lambda: mock
        return calls

    yield install
    app.dependency_overrides.pop(get_http, None)


@pytest.fixture
def keys(monkeypatch):
    s = get_settings()
    for k in ("openweather_api_key", "google_places_api_key", "google_maps_api_key"):
        monkeypatch.setattr(s, k, "test-key")
    weather._cache.clear()
    places._cache.clear()
    maps._cache.clear()
    yield s


def dest_id(client, name):
    return client.get("/api/destinations/search", params={"q": name}).json()["items"][0]["id"]


# ---- weather ------------------------------------------------------------------------------
def owm_handler(request):
    now = int(time.time())
    if request.url.path.endswith("/weather"):
        return httpx.Response(200, json={"main": {"temp": 14.2, "feels_like": 13.1, "humidity": 70},
                                         "weather": [{"main": "Clouds", "description": "broken clouds", "icon": "04d"}],
                                         "wind": {"speed": 3.4}})
    slots = [{"dt": now + h * 3600, "main": {"temp_min": 8 + h % 5, "temp_max": 15 + h % 4},
              "weather": [{"main": "Rain" if h >= 24 else "Clear", "icon": "10d" if h >= 24 else "01d"}],
              "pop": 0.8 if h >= 24 else 0.0} for h in range(0, 72, 3)]
    return httpx.Response(200, json={"city": {"timezone": 19800}, "list": slots})


def test_weather_fallback_without_key(client, seeded):
    w = client.get(f"/api/weather/{dest_id(client, 'Manali')}").json()
    assert w["source"] == "fallback" and w["current"] is None
    assert "not configured" in w["note"] and w["seasonal"]["summary"]


def test_weather_live_parsed_and_cached(client, seeded, keys, mock_http):
    calls = mock_http(owm_handler)
    did = dest_id(client, "Manali")
    w = client.get(f"/api/weather/{did}").json()
    assert w["source"] == "live" and w["current"]["temperature"] == 14.2
    assert w["current"]["weather_condition"] == "Clouds"
    assert len(w["forecast"]) >= 3
    assert any(d["rain_likely"] for d in w["forecast"]) and not w["forecast"][0]["rain_likely"]
    assert all("appid" in str(c.url) for c in calls)
    client.get(f"/api/weather/{did}")
    assert len(calls) == 2  # second request served from cache


@pytest.mark.parametrize("response, reason", [
    (httpx.Response(401, json={}), "rejected the API key"),
    (httpx.Response(429, json={}), "rate limit"),
    (httpx.Response(500, text="oops"), "error (500)"),
])
def test_weather_errors_fall_back(client, seeded, keys, mock_http, response, reason):
    mock_http(lambda r: response)
    w = client.get(f"/api/weather/{dest_id(client, 'Goa')}").json()
    assert w["source"] == "fallback" and reason in w["note"]


def test_weather_timeout_falls_back(client, seeded, keys, mock_http):
    def boom(request):
        raise httpx.ReadTimeout("slow", request=request)

    mock_http(boom)
    w = client.get(f"/api/weather/{dest_id(client, 'Goa')}").json()
    assert w["source"] == "fallback" and "timed out" in w["note"]


def test_weather_unknown_destination(client, seeded):
    assert client.get("/api/weather/9999").status_code == 404


# ---- places -------------------------------------------------------------------------------
def test_places_seeded_sorted_and_filtered(client, seeded):
    r = client.get(f"/api/places/{dest_id(client, 'Jaipur')}", params={"kind": "restaurant"}).json()
    assert r["source"] == "seeded" and r["items"]
    assert all(p["kind"] == "restaurant" for p in r["items"])
    d = [p["distance_km"] for p in r["items"]]
    assert d == sorted(d)
    assert client.get(f"/api/places/{dest_id(client, 'Jaipur')}", params={"kind": "spa"}).status_code == 422


def test_places_google_live_hides_key(client, seeded, keys, mock_http):
    def handler(request):
        assert request.headers["X-Goog-Api-Key"] == "test-key"
        assert json.loads(request.content)["includedTypes"] == ["restaurant"]
        return httpx.Response(200, json={"places": [{
            "id": "abc", "displayName": {"text": "Test Dhaba"}, "rating": 4.4, "formattedAddress": "MI Road",
            "location": {"latitude": 26.92, "longitude": 75.82}, "primaryType": "indian_restaurant",
            "photos": [{"name": "places/abc/photos/xyz"}]}]})

    mock_http(handler)
    r = client.get(f"/api/places/{dest_id(client, 'Jaipur')}", params={"kind": "restaurant"}).json()
    assert r["source"] == "google_places" and r["items"][0]["name"] == "Test Dhaba"
    assert r["items"][0]["photo"] == "/api/places/photo?name=places/abc/photos/xyz"
    assert "test-key" not in json.dumps(r)


def test_places_google_failure_uses_seeded(client, seeded, keys, mock_http):
    mock_http(lambda r: httpx.Response(503))
    r = client.get(f"/api/places/{dest_id(client, 'Jaipur')}", params={"kind": "attraction"}).json()
    assert r["source"] == "seeded" and "unavailable" in r["note"] and r["items"]


def test_photo_proxy_rejects_bad_names(client, keys):
    assert client.get("/api/places/photo", params={"name": "../../etc/passwd"}).status_code == 404


# ---- routes -------------------------------------------------------------------------------
def test_route_optimizer_vs_brute_force():
    # Heuristic, so assert on the distribution: measured ~96% optimal, mean gap ~0.1% (NN alone: ~5.5%).
    rng = random.Random(7)
    gaps = []
    for _ in range(100):
        pts = [(rng.uniform(26.8, 27.0), rng.uniform(75.7, 75.9)) for _ in range(7)]
        opt = RouteOptimizer(RouteOptimizer.calculate_distance_matrix(pts))
        res = opt.optimize()
        best = min(opt.calculate_total_distance([0, *p]) for p in itertools.permutations(range(1, 7)))
        assert res["order"][0] == 0 and sorted(res["order"]) == list(range(7))
        assert res["total_distance_km"] <= opt.calculate_total_distance(opt.nearest_neighbor()) + 1e-9
        gaps.append(res["total_distance_km"] / best - 1)
    assert sum(g < 1e-6 for g in gaps) >= 85
    assert sum(gaps) / len(gaps) < 0.01


def test_route_api_untangles_a_zigzag(client):
    # Four corners of a square visited in a crossing order.
    pts = [{"name": n, "latitude": la, "longitude": lo} for n, la, lo in
           [("Hotel", 26.90, 75.80), ("C", 26.92, 75.82), ("B", 26.90, 75.82), ("D", 26.92, 75.80)]]
    r = client.post("/api/routes/optimize", json={"points": pts, "return_to_start": True}).json()
    assert r["stops"][0]["name"] == "Hotel"
    assert r["total_distance_km"] < r["initial_distance_km"]
    assert r["distance_source"] == "estimate" and len(r["legs"]) == 4
    assert r["total_duration_minutes"] > 0
    bad = client.post("/api/routes/optimize", json={"points": pts, "start_index": 9})
    assert bad.status_code == 422


def test_google_route_matrix_parsed(client, keys, mock_http):
    def handler(request):
        n = len(json.loads(request.content)["origins"])
        return httpx.Response(200, json=[{"originIndex": i, "destinationIndex": j, "distanceMeters": 1000 * (i + j + 1),
                                          "duration": f"{60 * (i + j + 1)}s", "condition": "ROUTE_EXISTS"}
                                         for i in range(n) for j in range(n)])

    mock_http(handler)
    pts = [{"name": str(i), "latitude": 26.9 + i / 100, "longitude": 75.8} for i in range(3)]
    r = client.post("/api/routes/optimize", json={"points": pts}).json()
    assert r["distance_source"] == "google_routes"
    assert r["legs"][0]["distance_km"] == pytest.approx(1 + r["legs"][0]["from"] + r["legs"][0]["to"])


def test_public_config_without_keys(client):
    cfg = client.get("/api/config").json()
    assert cfg["maps"]["provider"] == "openstreetmap" and cfg["maps"]["browser_key"] is None
