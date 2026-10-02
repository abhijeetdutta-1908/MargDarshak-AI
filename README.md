# Margdarshak — AI-Based Smart Trip & Travel Planner

Margdarshak turns a traveller's budget, trip length, interests, dates and style into **one personalised plan**:
ranked destinations with plain-language explanations, a hotel, the weather, an optimised route, a day-wise
itinerary and a transparent cost estimate. Everything is saved to the user's account and can be shared by link.

> B.Tech major project. Full stack: React · FastAPI · PostgreSQL · Sentence Transformers · FAISS · Docker.

## Problem

Planning a trip today means hopping between sites: one to pick a destination, another for hotels, another for
weather, maps for routes, and a spreadsheet for the budget. Then the day-wise plan gets built by hand. Margdarshak
brings that whole workflow into one platform and explains each decision it makes.

## Features

| Area | What it does |
|------|--------------|
| **AI recommendations** | Hybrid engine: FAISS semantic search over Sentence-Transformer embeddings, then a 9-factor weighted score (interests, semantics, destination type, budget, duration, season, activities, hotels, popularity) with reasons, warnings and a confidence value |
| **Itinerary generator** | Picks attractions for your interests within each day's time budget. It schedules indoor places on rainy days, puts full-day excursions on dry days, keeps sunrise and evening events at the right time, places lunch near where you are, and skips places that are seasonally closed |
| **Route optimisation** | Nearest-neighbour, then alternating 2-opt and Or-opt over a distance matrix (Google Routes or a haversine estimate). Optimal in 96% of random test cases |
| **Budget calculator** | Accommodation, transport (including getting there from your city, with flights for long distances), food, activities and contingencies, as minimum, average and maximum, with the assumptions listed |
| **Hotels** | Ranked by budget fit, rating, tier preference and distance to your sights, with reasons |
| **Weather** | OpenWeather current conditions and a 5-day forecast, cached, with seasonal guidance as a labelled fallback |
| **Places & maps** | Google Places when a key is configured, otherwise the curated dataset. Google Maps or OpenStreetMap, with colour-coded day routes |
| **Trips** | Save, rename, duplicate, regenerate, share via a public read-only link, mark as travelled (builds travel history), delete |
| **Reviews** | One review per user per destination, edit or delete your own, averages and star distribution |
| **Admin** | CRUD for destinations and hotels (the recommender refreshes immediately), user roles, review moderation |
| **Fallback mode** | The whole app works with **no API keys**. Every non-live value is labelled ("Seasonal guidance", "Curated data", "Sample data", "Estimated") |

## Architecture

```
React SPA (Vite, Tailwind)  ──►  nginx  ──/api──►  FastAPI
                                                    ├─ routers (validation only)
                                                    ├─ services (auth, trips, weather, places, maps, reviews, admin)
                                                    └─ app/ml engines: RecommendationEngine · ItineraryGenerator
                                                                       BudgetCalculator · RouteOptimizer · hotel ranking
                                                    │
                                     PostgreSQL ◄───┤──► OpenWeather · Google Places · Google Routes (optional)
                                                    └──► Sentence Transformers + FAISS (baked into the image)
```

**New here? Start with [docs/getting-started.md](docs/getting-started.md).**

More detail: [docs/architecture.md](docs/architecture.md) · [docs/ml.md](docs/ml.md) · [docs/database.md](docs/database.md) ·
[docs/api.md](docs/api.md) · viva prep: [docs/viva.md](docs/viva.md)

## Tech stack

**Frontend:** React 19, Vite, Tailwind CSS 4, React Router, Axios, Recharts, Leaflet / Google Maps JS, lucide icons, Sonner toasts
**Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PyJWT, bcrypt, httpx
**AI/ML:** Sentence Transformers (all-MiniLM-L6-v2), FAISS, scikit-learn (TF-IDF fallback), NumPy, pandas
**Data:** PostgreSQL 16 · **Ops:** Docker, Docker Compose, nginx, GitHub Actions

## Quick start (Docker)

```bash
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD and JWT_SECRET (32+ chars); API keys are optional
docker compose up --build
```

The first build downloads PyTorch (CPU) and the embedding model, so expect a few minutes. On start the
backend runs migrations, seeds the catalogue and warms the recommender.

| URL | What |
|-----|------|
| http://localhost:3000 | The web app |
| http://localhost:8000/docs | Swagger UI (try every endpoint) |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | OpenAPI spec (import into Postman) |

**Admin account:** set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` before starting, or promote an existing
account with:

```bash
docker compose exec backend python ../database/seed.py --make-admin you@example.com
```

## Environment variables

All variables are documented in [.env.example](.env.example). The essentials:

| Variable | Required | Purpose |
|----------|----------|---------|
| `POSTGRES_PASSWORD` | yes | Database password (Compose builds `DATABASE_URL` from it) |
| `JWT_SECRET` | yes | 32+ character signing secret for access tokens |
| `OPENWEATHER_API_KEY` | no | Live weather; otherwise seasonal guidance |
| `GOOGLE_PLACES_API_KEY` / `GOOGLE_MAPS_API_KEY` | no | Live nearby places and route distances; otherwise curated data and estimates |
| `GOOGLE_MAPS_BROWSER_KEY` | no | Google Maps in the browser (a separate, referrer-restricted key); otherwise OpenStreetMap |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | no | Admin bootstrap |
| `RECOMMENDATION_WEIGHTS` | no | JSON to retune the scoring weights |

Secret keys never reach the browser. Place photos are proxied through the backend, and the only key the frontend
sees is the browser Maps key, which is meant to be public but referrer-restricted.

## Running locally without Docker

```bash
docker compose up postgres -d            # just the database, on localhost:5433

cd backend
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-ml.txt   # ML extras optional: falls back to TF-IDF
# set DATABASE_URL=postgresql+psycopg://margdarshak:<password>@localhost:5433/margdarshak and JWT_SECRET
alembic upgrade head
python ../database/seed.py
uvicorn app.main:app --reload            # http://localhost:8000

cd ../frontend
npm install
npm run dev                              # http://localhost:5173, proxies /api to :8000
```

Optional: prebuild the semantic index (the backend uses it when it matches the catalogue):

```bash
python ml/create_embeddings.py && python ml/build_faiss_index.py
python ml/recommendation_engine.py --budget 20000 --days 4 --type mountain --interests trekking nature --month 11
```

## Testing

```bash
cd backend && pytest                    # 85 tests, SQLite in-memory, no network
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5433/margdarshak_test pytest   # same suite on PostgreSQL
RUN_ST_TESTS=1 pytest -k sentence       # exercises the real Sentence-Transformer model
cd frontend && npm test && npm run lint  # 21 component/unit tests
ruff check .                             # backend lint (from repo root)
```

The backend tests cover:
- auth, JWT tampering, rate limits and security headers;
- the dataset's integrity;
- recommendations across many preference combinations;
- the budget maths and the route optimiser against brute force;
- itinerary rules: weather, time of day, closures, excursions and vegetarian preference;
- the trip lifecycle and access control, reviews and admin;
- external APIs with mocked HTTP for the live, error, timeout, rate-limit and fallback paths.

## CI/CD

`.github/workflows/ci.yml` runs on every push and pull request:
1. **Backend:** ruff, an Alembic upgrade/downgrade round-trip, then pytest against a PostgreSQL service.
2. **Frontend:** ESLint, Vitest, then a production build.
3. **Docker:** builds both images. On `main` it pushes them to GHCR (`ghcr.io/<owner>/margdarshak-{backend,frontend}`).

### Deploying (optional, AWS)

The images are ready to run anywhere. On one EC2 instance, the steps are:
1. Install Docker.
2. Copy `docker-compose.yml` and `.env`.
3. Point the `backend`/`frontend` services at the GHCR images.
4. Run `docker compose up -d` behind HTTPS (an ALB or Caddy/nginx with Let's Encrypt).

For managed hosting, use ECS Fargate for the two services and RDS for PostgreSQL. In production, don't publish
port 8000; only nginx should reach the backend.

## Project layout

```
backend/            FastAPI app
  app/routers/      HTTP layer (validation, auth dependencies)
  app/services/     business logic and external API clients
  app/ml/           recommendation, itinerary, budget, route and hotel engines (framework-free)
  app/models/       SQLAlchemy models        app/schemas/  Pydantic schemas
  tests/            pytest suite
frontend/           React app (pages, components, hooks, services), nginx.conf
ml/                 datasets/ (CSV), create_embeddings.py, build_faiss_index.py, recommendation_engine.py
database/           seed.py, migrations/ (Alembic)
docs/               architecture, api, ml, database, viva
```

## Data honesty

- Destinations and places are hand-written for this project (see [ml/datasets/README.md](ml/datasets/README.md)).
- Costs are planning estimates. Hotels are generated sample listings, and the UI says so.
- Live data appears only when API keys are configured, and anything not live carries a label.

## Limitations & future scope

**Current limits:**
- The catalogue covers 36 destinations.
- There's no booking or payment.
- The time-of-day and closure rules depend on hand-tagged data.
- Rate limits and caches are per process.

**Future scope:** the architecture leaves room for each of these:
- booking and payment integration;
- flight and train search;
- a conversational assistant (an LLM that calls the existing engines as tools);
- group trips with shared editing;
- real-time traffic;
- learning user preferences from feedback.
