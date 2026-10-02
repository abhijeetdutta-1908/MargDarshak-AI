# Margdarshak — AI-Based Smart Trip & Travel Planner

Margdarshak turns your budget, duration, interests and travel dates into one personalized plan: ranked
destinations with explanations, hotels, weather, an optimized route, a day-wise itinerary and a cost estimate.

> **Status:** Phase 1 of 11 (foundation). See [docs/architecture.md](docs/architecture.md) for the architecture
> and phase plan.

## Tech stack

React + Vite + Tailwind · FastAPI + SQLAlchemy + Pydantic · PostgreSQL · Sentence Transformers + FAISS +
scikit-learn · OpenWeather, Google Maps/Places · Docker Compose

## Quick start (Docker)

```bash
cp .env.example .env    # then set POSTGRES_PASSWORD and JWT_SECRET
docker compose up --build
```

| URL | What |
|-----|------|
| http://localhost:3000 | Web app (shows live Frontend → Backend → PostgreSQL status) |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/api/health | Health check (`503` if the database is down) |

## Local development (without Docker for app code)

Run Postgres only: `docker compose up postgres -d`, then:

```bash
# backend
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows; use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg://margdarshak:<password>@localhost:5432/margdarshak
uvicorn app.main:app --reload

# frontend (new terminal) — dev server proxies /api to :8000
cd frontend
npm install
npm run dev     # http://localhost:5173
```

## Tests

```bash
cd backend && pytest
```

## Environment variables

See [.env.example](.env.example). API keys are optional; without them the app uses seeded data and labels it
as such. Never commit `.env`.

## Project layout

```
backend/    FastAPI app (app/), tests/
frontend/   React app (src/), nginx.conf for the Docker build
ml/         embedding + FAISS build scripts, datasets        (Phase 4)
database/   seed script, migrations                          (Phases 2–3)
docs/       architecture, api, ml, database, viva notes
```
