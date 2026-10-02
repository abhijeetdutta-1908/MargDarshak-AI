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
| postgres | postgres:16-alpine   | 5432        | volume `pgdata`, healthcheck gates backend |
| backend  | python:3.12-slim     | 8000        | uvicorn, `/docs`, `/redoc`             |
| frontend | nginx:1.27-alpine    | 3000        | static build, proxies `/api/` → backend |

## Development phases

| # | Phase | Deliverable | Status |
|---|-------|-------------|--------|
| 1 | Setup | Repo layout, FastAPI + React + Postgres, Docker Compose, health check end to end | ✅ done |
| 2 | Auth & models | All SQLAlchemy models, Alembic migrations, register/login/JWT/me, preferences API | |
| 3 | Data | Seed script: 30+ destinations, 100+ hotels, 100+ attractions, 50+ restaurants | |
| 4 | Recommendations | Sentence-Transformer embeddings (TF-IDF fallback), FAISS index, weighted scoring + reasons | |
| 5 | External APIs | Weather, Maps, Places services with cache, timeouts, fallbacks | |
| 6 | Budget & routes | `BudgetCalculator`, `RouteOptimizer` | |
| 7 | Itinerary | `ItineraryGenerator`, weather-aware, `/api/trips/generate` | |
| 8 | Product UI | Landing, dashboard, plan-trip wizard, results, trip/itinerary pages, saved trips, reviews | |
| 9 | Admin | Role-protected CRUD for destinations/hotels, review moderation | |
| 10 | Hardening | Tests across engines/APIs, rate limiting, indexes, pagination | |
| 11 | Ship | GitHub Actions CI, full README + docs (api/ml/database/viva) | |

Each phase ends with: code runs, tests pass, summary of what was built.
