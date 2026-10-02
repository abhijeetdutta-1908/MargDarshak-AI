# Getting started

Margdarshak runs as three pieces:

| Piece | What it is | Address |
|-------|-----------|---------|
| **frontend** | React web app, served by nginx | http://localhost:3000 |
| **backend** | FastAPI service: auth, AI recommendations, itinerary, budget | http://localhost:8000 (API docs at `/docs`) |
| **postgres** | Database | `localhost:5433` |

There are two ways to run it:
- **[Option A: Docker](#option-a-docker-recommended).** One command starts everything. Use this to run or demo the project.
- **[Option B: Local dev](#option-b-local-development-without-docker).** Run the backend and frontend yourself, with hot reload, while you change code.

---

## 1. Prerequisites

| Tool | Needed for | Check |
|------|------------|-------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running) | Option A, and the database in Option B | `docker compose version` |
| Git | cloning | `git --version` |
| Python 3.12+ | Option B only | `python --version` |
| Node.js 22+ | Option B only | `node --version` |

---

## 2. Environment variables

All settings live in a `.env` file in the project root. Start from the template:

```bash
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead.

### Required

| Variable | What to put | Example |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Any password for the database | `my-db-pass-123` |
| `JWT_SECRET` | A random string of **32+ characters**, used to sign login tokens | generate it with the command below |
| `DATABASE_URL` | Only for Option B. Uses the same password as `POSTGRES_PASSWORD` | `postgresql+psycopg://margdarshak:my-db-pass-123@localhost:5433/margdarshak` |

Generate a JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> If `POSTGRES_PASSWORD` or `JWT_SECRET` is missing, `docker compose up` stops immediately and says which one.

### Optional

Without any API keys the app still works fully. It uses clearly labelled fallbacks: seasonal weather guidance,
curated places, estimated distances and OpenStreetMap.

| Variable | Default | Purpose |
|----------|---------|---------|
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | empty | Creates (or promotes) an admin account on startup |
| `OPENWEATHER_API_KEY` | empty | Live weather and 5-day forecast |
| `GOOGLE_PLACES_API_KEY` | empty | Live nearby restaurants and attractions |
| `GOOGLE_MAPS_API_KEY` | empty | Live road distances and travel times (Routes API) |
| `GOOGLE_MAPS_BROWSER_KEY` | empty | Google Maps in the browser. Use a **separate** key restricted to your site's URL; without it the map uses OpenStreetMap |
| `POSTGRES_USER`, `POSTGRES_DB` | `margdarshak` | Database user and name |
| `POSTGRES_HOST_PORT` | `5433` | Host port for Postgres (5433 avoids clashing with a locally installed Postgres) |
| `ACCESS_TOKEN_MINUTES` | `1440` | Login session length |
| `RATE_LIMIT_ENABLED` | `true` | Limits on login, sign-up and AI endpoints |
| `CORS_ORIGINS` | `http://localhost:5173` | Only needed if the frontend runs on another origin |
| `RECOMMENDATION_WEIGHTS` | empty | JSON to retune AI scoring, e.g. `{"budget": 0.3}` |

A minimal working `.env`:

```env
POSTGRES_PASSWORD=my-db-pass-123
JWT_SECRET=paste-the-generated-48-character-secret-here
DATABASE_URL=postgresql+psycopg://margdarshak:my-db-pass-123@localhost:5433/margdarshak
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin-pass-123
```

> Never commit `.env`. It's already in `.gitignore` and excluded from Docker images.

---

## Option A: Docker (recommended)

From the project root:

```bash
docker compose up --build
```

- **First run:** takes a few minutes. It downloads PyTorch (CPU) and the AI embedding model, which are then baked into the image.
- **Every start:** the backend applies database migrations, loads the 36 destinations, 293 places and 180 hotels, and warms up the AI model.
- **Ready:** when all three services show as running, open **http://localhost:3000**. Register an account, or sign in with your `ADMIN_EMAIL`.

Everyday commands:

| Task | Command |
|------|---------|
| Start in the background | `docker compose up -d` |
| See status | `docker compose ps` |
| Follow backend logs | `docker compose logs -f backend` |
| Stop | `docker compose down` |
| Stop **and delete all data** | `docker compose down -v` |
| Rebuild after code changes | `docker compose up --build -d` |
| Make an existing user admin | `docker compose exec backend python ../database/seed.py --make-admin you@example.com` |
| Re-apply dataset changes (CSV edits) | `docker compose exec backend python ../database/seed.py --update`, then `docker compose restart backend` |

---

## Option B: Local development (without Docker)

**1. Start only the database.** If the full Docker stack is running, stop its backend and frontend first so
ports 8000 and 3000 are free:

```bash
docker compose stop backend frontend
docker compose up -d postgres
```

**2. Backend.** Open a terminal in the project root.

macOS / Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-ml.txt
cp ../.env .env
alembic upgrade head
python ../database/seed.py
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-ml.txt
Copy-Item ..\.env .env
alembic upgrade head
python ..\database\seed.py
uvicorn app.main:app --reload
```

What each step does:
- `requirements-ml.txt` is optional. It adds Sentence Transformers and FAISS; without it the AI falls back to TF-IDF.
- The backend reads `.env` from the folder you run it in, which is why it's copied into `backend/`. Check that `DATABASE_URL` points at `localhost:5433`.
- `alembic upgrade head` creates the tables.
- `seed.py` loads the travel data.
- In this mode `ADMIN_EMAIL`/`ADMIN_PASSWORD` aren't applied automatically. Register in the app, then run
  `python ../database/seed.py --make-admin you@example.com` from `backend/`.

The API is now at http://localhost:8000/docs.

**3. Frontend.** Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server forwards `/api` calls to the backend on port 8000.

> If port 5173 is busy, choose another. On macOS/Linux run `PORT=5174 npm run dev`; in PowerShell run `$env:PORT=5174; npm run dev`.

---

## 3. Check it works

| Check | Expected |
|-------|----------|
| http://localhost:8000/api/health | `{"status":"ok","database":"ok", ...}` |
| http://localhost:8000/docs | Swagger page listing every endpoint |
| The web app → **Plan trip** → *Get AI recommendations* | Ranked destinations with scores and reasons |
| Pick one → **Plan this trip** | A full plan: map, day-wise itinerary, hotel, weather, budget |

---

## 4. Run the tests

Run each line from the project root (backend commands need the Option B virtualenv active):

```bash
ruff check .                         # backend lint
cd backend; pytest; cd ..            # 85 backend tests, no database or internet needed
cd frontend; npm test; npm run lint; cd ..   # 21 frontend tests + lint
```

---

## 5. Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to the Docker daemon` / `dockerDesktopLinuxEngine` | Start Docker Desktop and wait until it says it's running |
| `set POSTGRES_PASSWORD in .env` or `set JWT_SECRET` | Fill those in `.env` (the secret needs 32+ characters) |
| `password authentication failed` (Option B) | `DATABASE_URL` must use port **5433** and the same password as `POSTGRES_PASSWORD` |
| Changed `POSTGRES_PASSWORD` after the first run, and now the DB rejects it | The old password is stored in the data volume. Run `docker compose down -v` to wipe it and start fresh |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again |
| Port 3000, 8000 or 5433 already in use | Stop the other program, or change the port: `POSTGRES_HOST_PORT` in `.env`, or the `ports:` lines in `docker-compose.yml` |
| Weather says "Seasonal guidance" | Expected without `OPENWEATHER_API_KEY`; add one for live weather |
| `Too many requests` | Rate limit hit; wait a minute (or set `RATE_LIMIT_ENABLED=false` for local testing) |

Further reading: [README](../README.md) · [architecture](architecture.md) · [API](api.md) · [ML](ml.md) · [database](database.md) · [viva guide](viva.md)
