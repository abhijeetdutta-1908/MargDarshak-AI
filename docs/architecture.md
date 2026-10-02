# Architecture

## Three layers

```
┌──────────────────────────── Presentation ────────────────────────────┐
│ React 19 SPA (Vite, Tailwind 4, React Router, Recharts, Leaflet/Google Maps) │
│ pages → hooks (useApi, useGenerateTrip) → services/api.js (Axios)    │
└───────────────────────────────┬──────────────────────────────────────┘
                     nginx: static files, CSP, gzip, /api proxy
┌───────────────────────────────▼──────────── Business ────────────────┐
│ FastAPI                                                              │
│  routers/   validation (Pydantic), auth dependencies, rate limits    │
│  services/  users · catalog · recommendations · trips · weather ·    │
│             places · maps · reviews · admin · http (shared client)   │
│  ml/        RecommendationEngine · ItineraryGenerator ·              │
│             BudgetCalculator · RouteOptimizer · rank_hotels ·        │
│             Embedder/VectorIndex (Sentence Transformers + FAISS)     │
└──────────────┬───────────────────────────────┬───────────────────────┘
┌──────────────▼──────── Data ───────┐  ┌──────▼──── External (optional) ────┐
│ PostgreSQL 16 (SQLAlchemy, Alembic)│  │ OpenWeather · Google Places (New) ·│
│ ml/datasets CSV → seed.py          │  │ Google Routes · Google Maps JS     │
│ ml/artifacts embeddings + FAISS    │  │ (each has a labelled fallback)     │
└────────────────────────────────────┘  └────────────────────────────────────┘
```

**Rules the code follows:**
- Routers hold no business logic.
- The ML engines import nothing from FastAPI or the ORM; services translate ORM rows into engine dataclasses.
  That keeps the engines unit-testable, and runnable from the CLI (`ml/recommendation_engine.py`).
- Every external call goes through `services/http.request_json`. It handles the timeout, error mapping
  (401/403 key rejected, 429 rate limit, timeout, unreachable) and caching. Each caller decides on a labelled
  fallback, and each response carries `source` (`live`, `google_places`, `google_routes`, `forecast` versus
  `fallback`, `seeded`, `sample`, `estimate`).

## Trip generation flow (`POST /api/trips/generate`)

```
validate (Pydantic) ─► RecommendationEngine.rank_destinations (top 5, for "other good matches")
  ─► destination = requested id or the top recommendation
  ─► rank_hotels (budget fit, rating, tier, distance to sights) ─► chosen hotel
  ─► weather.get_weather (OpenWeather, cached 30 min) ─► day_outlook per date (forecast or seasonal)
  ─► places from the DB ─► ItineraryGenerator
        closures ─► selection ─► weather swaps ─► grouping ─► RouteOptimizer per day
        ─► time slots, meals, free time ─► carry-over
  ─► BudgetCalculator (chosen hotel price, itinerary activity cost, intercity km from origin)
  ─► persist saved_trips + trip_days + itinerary_items (as a draft) ─► TripOut
```

Regenerate reruns the planning steps with `variation + 1`. That shuffles tie-breaks, rotates day groups and
alternates restaurants, and it refreshes the weather. Destination and hotel stay the same.

## Caching and performance

| What | Where | Lifetime |
|------|-------|----------|
| Recommendation engine (embeddings + FAISS index) | process memory | until an admin changes the catalogue (`invalidate_catalog()`) |
| Model and prebuilt vectors | Docker image (`/srv/models`, `ml/artifacts`) | per build; used only on fingerprint match |
| Weather | TTL cache per destination | 30 minutes |
| Google Places / Routes | TTL cache per location, kind or point set | 6 hours |
| Frontend assets | nginx `immutable` | 1 year (content-hashed) |

Other performance measures:
- The engine is warmed in the FastAPI lifespan.
- Recommendations return in about 100 ms, and trip generation in under 200 ms without live APIs.
- Pages are code-split per route, and lists are paginated.
- Every foreign key and filter column is indexed.

## Security

- **Passwords:** bcrypt; length and complexity are validated.
- **Tokens:** HS256 JWTs, with a 32+ character secret enforced at startup. Token versioning makes logout and
  password changes revoke existing tokens.
- **Authorisation:**
  - Other users' trips return 404.
  - Reviews can be changed only by their owner or an admin.
  - The whole admin router requires the admin role.
- **Injection:** SQLAlchemy binds every parameter, and LIKE wildcards are escaped. Pydantic validates every input
  (Literal vocabularies, numeric ranges, lengths).
- **Rate limits:** sliding window on login, register, recommendations and generation, keyed by IP via nginx's
  `X-Real-IP`.
- **Headers:** nosniff, `X-Frame-Options: DENY`, Referrer-Policy and Permissions-Policy, plus a strict CSP that lists
  only the origins the app uses. The API responses are `no-store`.
- **Secrets:** server-side keys never reach the browser. Place photos are proxied, with path validation. The browser
  Maps key is a separate, referrer-restricted key. `.env` is git- and docker-ignored.
- **Errors:** database errors return a friendly 503, and any unhandled exception returns a generic 500. Tracebacks
  are logged, never returned.

## Runtime topology (docker compose)

| Service | Image | Host port | Notes |
|---------|-------|-----------|-------|
| postgres | postgres:16-alpine | 5433 | `pgdata` volume, healthcheck |
| backend | python:3.12-slim + CPU torch + model | 8000 | on start: `alembic upgrade head`, then `seed.py`, then uvicorn; healthcheck on `/api/health` |
| frontend | nginx:1.27-alpine | 3000 | serves the build and proxies `/api/` to the backend; waits for a healthy backend |

## Development phases

| # | Phase | Delivered |
|---|-------|-----------|
| 1 | Setup | Repo layout, FastAPI + React + Postgres, Compose, health check end to end |
| 2 | Auth & models | 11 SQLAlchemy models, Alembic, JWT auth, profile, preferences, login/register/profile UI |
| 3 | Data | 36 destinations, 293 places, 180 sample hotels, idempotent seed, catalogue API |
| 4 | Recommendations | Sentence Transformers + FAISS (with fallbacks), 9-factor score, explanations |
| 5 | External APIs | OpenWeather, Google Places, Google Routes, caching, error mapping, fallbacks |
| 6 | Budget & routes | BudgetCalculator, RouteOptimizer (NN + 2-opt + Or-opt) |
| 7 | Itinerary | Weather-aware ItineraryGenerator, hotel ranking, trip API, dashboard |
| 8 | Product UI | All pages, maps, charts, saved trips, sharing, reviews, tests |
| 9 | Admin | Admin API and UI, admin bootstrap |
| 10 | Hardening | Rate limits, headers/CSP, safe errors, security tests, PostgreSQL test run |
| 11 | Ship | GitHub Actions CI/CD, documentation |
