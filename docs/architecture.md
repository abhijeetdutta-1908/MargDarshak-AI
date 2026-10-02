# Architecture & Development Plan

## Layers

```
React (Vite, Tailwind)  ── served by nginx, /api proxied ──┐
                                                           ▼
FastAPI  ── routers (thin) ── services (business logic) ── ml/ (engines)
   │                                │
   ▼                                ▼
PostgreSQL (SQLAlchemy)     External APIs: OpenWeather, Google Maps/Places
                            (each with a clearly-labelled fallback)
```

- **Routers** only validate input (Pydantic) and call services. No business logic in routes.
- **Services**: auth, recommendations, itinerary, budget, routes, weather, places, hotels, trips.
- **Engines** (`RecommendationEngine`, `ItineraryGenerator`, `BudgetCalculator`, `RouteOptimizer`) are plain Python classes with no FastAPI imports, so they are unit-testable in isolation.
- **Fallbacks**: every external call has a timeout and a seeded-data fallback. Responses carry a `source` field (`"live"` / `"fallback"`) so the UI never presents seeded data as live.

## Request flow — `POST /api/trips/generate`

```
preferences → RecommendationEngine (FAISS candidates → weighted score + reasons)
            → pick destination → weather → places/attractions → hotels (ranked)
            → RouteOptimizer (distance matrix → nearest neighbour → 2-opt)
            → ItineraryGenerator (weather-aware slotting) → BudgetCalculator
            → persist SavedTrip / TripDays / ItineraryItems → response
```

## Runtime topology (docker compose)

| Service  | Image                | Port (host) | Notes                                  |
|----------|----------------------|-------------|----------------------------------------|
| postgres | postgres:16-alpine   | 5433        | volume `pgdata`, healthcheck gates backend |
| backend  | python:3.12-slim     | 8000        | uvicorn, `/docs`, `/redoc`             |
| frontend | nginx:1.27-alpine    | 3000        | static build, proxies `/api/` → backend |

## Development phases

| # | Phase | Deliverable | Status |
|---|-------|-------------|--------|
| 1 | Setup | Repo layout, FastAPI + React + Postgres, Docker Compose, health check end to end | ✅ done |
| 2 | Auth & models | All SQLAlchemy models, Alembic migrations, register/login/JWT/me, preferences API, login/register/profile UI | ✅ done |
| 3 | Data | 36 destinations, 153 attractions, 68 restaurants, 72 activities/shopping, 180 sample hotels; idempotent seed; destinations + hotels API | ✅ done |
| 4 | Recommendations | Sentence-Transformer embeddings (TF-IDF fallback), FAISS index (NumPy fallback), 9-component weighted score, reasons/warnings, `POST /api/recommendations` | ✅ done |
| 5 | External APIs | OpenWeather, Google Places (New), Google Routes matrix; TTL cache, timeouts, error mapping, labelled fallbacks; photo proxy | ✅ done |
| 6 | Budget & routes | `BudgetCalculator` (min/avg/max, intercity, assumptions), `RouteOptimizer` (NN + 2-opt + Or-opt), `POST /api/routes/optimize` | ✅ done |
| 7 | Itinerary | `ItineraryGenerator` (interest scoring, weather swaps, excursion days, time-of-day rules, carry-over), hotel ranking, `/api/trips/*` incl. regenerate/share/duplicate/complete, dashboard API | ✅ done |
| 8 | Product UI | Landing, dashboard, plan trip, explained recommendations, destination/hotel/trip/itinerary pages, maps (Google or OSM), budget charts, saved trips, sharing, reviews; responsive; 21 frontend tests | ✅ done |
| 9 | Admin | `/api/admin/*`: destinations + hotels CRUD (recommender cache invalidated), users, review moderation; admin bootstrap via seed | ✅ done |
| 10 | Hardening | Rate limiting, security headers + CSP, safe 500s, token tampering tests, suite also runs on PostgreSQL (85 backend tests) | ✅ done |
| 11 | Ship | GitHub Actions CI, full README + docs (api/ml/database/viva) | |

Each phase ends with: code runs, tests pass, summary of what was built.
