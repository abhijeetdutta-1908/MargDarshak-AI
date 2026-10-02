# Viva guide — Margdarshak

## Problem statement

Trip planning is manual and fragmented. A traveller compares destinations on one site, hotels on another, checks
weather separately, estimates costs in a spreadsheet, looks up routes on a map, and finally writes a day-wise
plan by hand. None of these tools knows about the others, so the plan rarely accounts for budget, season, weather
and travel time together.

**Margdarshak** ("the one who shows the way") collects the traveller's preferences once and produces a single,
explained, personalised plan: destination, hotel, weather, optimised route, day-wise itinerary and budget.

## Objectives

1. Recommend destinations that match a user's interests, budget, duration and season, and **explain why**.
2. Recommend a suitable hotel and estimate the full trip cost transparently.
3. Generate a realistic day-wise itinerary that adapts to the weather and minimises travel.
4. Integrate weather, places and maps, while staying fully usable without any paid API (labelled fallbacks).
5. Deliver it as a secure, tested, deployable web application.

## Methodology

1. **Data:** a hand-written catalogue of 36 Indian destinations and 293 places. Each has coordinates, tags,
   best months, ideal trip length, cost profile, indoor/outdoor flag and visit duration. 180 generated sample
   hotels are labelled as samples.
2. **Representation:** each destination becomes a text, then a Sentence-Transformer embedding, stored in a FAISS
   index. User preferences become a query text and an embedding.
3. **Recommendation:** semantic retrieval, then content-based scoring on nine interpretable factors, then a
   weighted rank and generated reasons.
4. **Planning:** hotel ranking, then weather lookup, then attraction selection, weather-aware day grouping, route
   optimisation per day, and timeline construction. The budget is calculated last.
5. **Engineering:**
   - a REST API with JWT auth;
   - PostgreSQL with migrations;
   - a React UI;
   - Docker;
   - CI with 85 backend tests and 21 frontend tests.

## Architecture in one breath

The React SPA talks to nginx, which proxies `/api` to FastAPI. Routers only validate. Services hold the business
logic and call framework-free ML engines in `app/ml`. Data lives in PostgreSQL. External APIs (OpenWeather,
Google Places and Routes) are optional, each with a labelled fallback. See [architecture.md](architecture.md).

## Why these technologies?

| Choice | Reason |
|--------|--------|
| **FastAPI** | Async I/O for parallel external API calls, Pydantic validation and automatic OpenAPI docs (`/docs`), and it's Python, so the API and the ML share one language and process |
| **React** | Component reuse (one TripView powers the trip, itinerary and shared pages), a large ecosystem (Recharts, Leaflet) and fast iteration with Vite |
| **PostgreSQL** | Relational integrity for users, trips, days and items (FKs, cascades, unique and check constraints), JSONB for snapshots, and it's production-grade and free |
| **Sentence Transformers** | Captures meaning, not just keywords: "peaceful hill station with tea gardens" matches Darjeeling without shared words. MiniLM-L6 is small (about 90 MB, 384-dimensional) and fast on CPU, and runs offline |
| **FAISS** | Standard, very fast vector search. IndexFlatIP gives exact cosine search now and scales to millions of vectors by switching index type, without code changes elsewhere |
| **scikit-learn TF-IDF** | A dependable fallback when the transformer model isn't available, so the app never depends on a downloaded model or external LLM |
| **Docker Compose** | One command (`docker compose up --build`) brings up the database, API (with model baked in) and frontend identically everywhere |

## How recommendation scoring works

There are nine components, each in [0, 1]:

| Component | Weight |
|-----------|--------|
| interest match | 0.20 |
| semantic similarity | 0.10 |
| destination type | 0.15 |
| budget fit | 0.20 |
| duration fit | 0.10 |
| season | 0.10 |
| activities available | 0.05 |
| hotel availability | 0.05 |
| popularity | 0.05 |

`score = 100 × Σ weight × component`. An off-season trip has its score multiplied by 0.8.

**Example.** A mountain trip with trekking, nature and photography, ₹20,000, 4 days, 2 people, November.
Manali scores:
- interest 1.0, since all three interests match its tags;
- type 1.0, since its category is mountain;
- budget 1.0, since the estimate is ₹19,472, under budget;
- duration 1.0, since 4 days is within its ideal 3–6;
- season 1.0, since November is a best month.

That gives roughly 99/100, with reasons such as "Strong match for your mountain preference" and "Fits your budget".

**Confidence** grows with how much the user told us: `score/100 × (0.5 + 0.1 × signals given)`.

Full formulas are in [ml.md](ml.md).

## How route optimisation works

The problem is a small Travelling Salesman Problem, which is NP-hard in general.
1. Build a distance matrix: Google Routes, or haversine × 1.3 road factor.
2. **Nearest neighbour** from the hotel builds a quick greedy tour.
3. **2-opt** reverses any sub-path whose reversal shortens the tour; this removes crossings.
4. **Or-opt** moves runs of 1–3 stops elsewhere.
5. Alternate 3 and 4 until neither improves.

On 600 random cases of 5–8 stops, this is optimal 96% of the time, with a mean gap of 0.11%. Nearest neighbour
alone averages a 5.5% gap and can be 43% worse.

## How weather affects the itinerary

- **Per-day outlook:**
  - Within the 5-day OpenWeather window, a day is rain-likely when the daytime rain probability is 50% or more, or
    the conditions are Rain, Drizzle, Thunderstorm or Snow.
  - Beyond the window, a monsoon month (June–September) outside the destination's best season counts as rain-likely.
- **Rainy days:**
  - Indoor places (museums, palaces, forts with galleries) are scheduled first.
  - If too few indoor places were picked, the weakest outdoor picks are swapped for indoor ones.
  - Treks, beaches and full-day excursions are moved to dry days.
- The plan **explains** what it did. If a destination has no indoor sights (e.g. Manali), it says so honestly and
  advises keeping that day flexible.

## Other design points worth mentioning

- **Time-of-day realism:**
  - sunrise spots get an early start with breakfast afterwards, never on arrival day;
  - evening events (Ganga aarti, Wagah ceremony, dance shows) are scheduled at 17:30 or later;
  - full-day excursions start at 07:00, include travel in their duration, and skip a separate lunch.
- **Seasonal closures:** places tagged `closed:11-4` (e.g. Rohtang Pass) are dropped on those dates, with an
  explanation.
- **Honesty:** every non-live value is labelled ("Seasonal guidance", "Curated data", "Sample data", "Estimated").
- **Security:**
  - bcrypt, JWT with token versioning (real logout), owner checks that return 404, an admin role and rate limits;
  - CSP and security headers, and no secrets in the browser.

## Limitations

- The catalogue is small (36 destinations) and hand-written. Costs are estimates, and hotels are samples.
- The time-of-day and closure rules depend on tags in the data.
- Without API keys, weather is seasonal guidance and distances are straight-line estimates.
- There's no booking, payment, or flight/train search.
- The recommender is content-based. It doesn't yet learn from user behaviour (no collaborative filtering).
- Rate limits and caches are per process, so scaling out would need Redis.

## Future scope

- Booking and payment integration (the `bookings` table already exists).
- Flight and train search for the intercity leg, and real-time traffic for routes.
- A conversational assistant: an LLM that calls the existing engines as tools, so answers stay grounded.
- Group trips with shared editing and voting; social travel planning.
- Collaborative filtering from saved trips and reviews; learning the weights from feedback.
- A voice interface; offline itinerary export (PDF or calendar).

---

## Likely viva questions

**Q1. What exactly is "AI" in this project?**
Two things. First, semantic understanding: Sentence-Transformer embeddings and FAISS vector search match
free-text preferences to destination descriptions by meaning. Second, an explainable ranking model that combines
nine interpretable signals computed from the data (the weights are expert-set; see Q8). The planning parts (routes, budgets, schedules) deliberately use deterministic
algorithms, because they are correct and verifiable, which an LLM wouldn't be.

**Q2. Why not just use ChatGPT to make the itinerary?**
- An LLM can invent places, prices and opening times, and can't guarantee a budget or an optimal route.
- Our engines give reproducible, testable results with real coordinates, explicit costs and stated assumptions.
- It also works offline and costs nothing per request.
- An LLM could be added later as a conversational front end that calls these engines.

**Q3. What is a sentence embedding? Why cosine similarity?**
A sentence embedding is a fixed-length vector (384 numbers here) produced by a transformer, so that texts with
similar meaning are close together. Cosine similarity measures the angle between vectors and ignores length. We
normalise vectors to unit length, so the inner product equals cosine, which is exactly what FAISS `IndexFlatIP`
computes.

**Q4. Why FAISS for only 36 destinations?**
It's correct now (exact search, under a millisecond) and future-proof: the same code scales to millions of places
by changing the index type. It also separates "retrieve candidates" from "score candidates", the standard
two-stage design used in real recommender systems.

**Q5. What if the model or FAISS isn't installed?**
The engine falls back automatically, to TF-IDF for embeddings and exact NumPy search for the index, and reports
which backend it used. CI deliberately runs the full test suite in this light mode.

**Q6. How do you prevent stale embeddings after an admin edits a destination?**
- The admin API calls `invalidate_catalog()`, so the engine rebuilds from the database on the next request.
- Prebuilt artifacts carry a SHA-256 fingerprint of all destination texts and are only reused when it matches.

**Q7. Is the recommendation content-based or collaborative?**
Content-based (with semantic similarity), because a new system has no interaction history: the cold-start
problem. With enough saved trips and reviews, collaborative signals could be added as another weighted component.

**Q8. How are the weights chosen? Aren't they arbitrary?**
They're an expert-set starting point, reflecting how much each factor matters to a traveller. They're
configurable through `RECOMMENDATION_WEIGHTS` and normalised automatically. The test suite pins the expected
behaviour across preference combinations, so any retuning is checked. With user feedback, the weights could be
learned (e.g. logistic regression on accepted versus ignored recommendations).

**Q9. Why the off-season penalty?**
In testing, Leh ranked first for a January adventure trip. Its type match outweighed the 10% season weight, even
though the passes are closed then. Multiplying off-season scores by 0.8 fixed this without hiding the
destination, and the warning tells the user why.

**Q10. What is 2-opt, and is your route optimal?**
2-opt takes two edges of a route and reconnects them the other way, which reverses the segment in between, and it
keeps doing this while the route gets shorter. It's a local search, so not guaranteed optimal. Combined with
Or-opt it was optimal in 96% of random tests, with a 0.11% average gap. Exact methods (Held–Karp, O(n²·2ⁿ)) are
unnecessary at this size.

**Q11. How do you estimate travel time without Google?**
Haversine distance × 1.3 road factor, divided by typical city speeds (16–26 km/h by mode), plus 5 minutes per leg.
Hops under 800 m are treated as walking. The UI labels these values "Estimated".

**Q12. How is the budget calculated?**
Accommodation (nights × rooms × nightly price) + local transport (by mode) + intercity (by distance, with flights
above 1,000 km) + food (by tier) + activities (the itinerary's actual entry fees) + 8% miscellaneous. Each component
has a min/max band, and the response lists every assumption.

**Q13. How is the hotel chosen?**
Score = 35% budget fit + 25% rating + 20% tier match + 20% closeness to the attractions' centroid. The nightly
budget is 45% of the trip budget ÷ nights ÷ rooms.

**Q14. How do you handle a failing external API?**
- Every call has a timeout (6 s) and maps errors to clear reasons: invalid key, rate limit, timeout, unreachable,
  bad response.
- The service then returns seeded or estimated data with `source` set and a note explaining why.
- Successful responses are cached (weather for 30 minutes, places and routes for 6 hours).
- Tests simulate each failure with a mocked HTTP transport.

**Q15. How is authentication secured?**
- Passwords are hashed with bcrypt and never stored in plain text.
- JWTs are signed with HS256 using a 32+ character secret. Each token carries the user's `token_version`;
  logout or a password change bumps it, revoking old tokens.
- Login and registration are rate-limited.
- Tests check forged signatures, expired tokens and `alg=none`.

**Q16. How do you stop one user seeing another user's trip?**
Every trip route loads the trip through `get_owned()`, which returns **404** (not 403) when the owner differs, so
trip IDs can't be probed. Shared trips use a random 128-bit token and can be revoked.

**Q17. How do you prevent SQL injection?**
SQLAlchemy always uses bound parameters, and search uses `icontains(..., autoescape=True)`, so `%` and `_` are
literal. A test sends `' OR 1=1; DROP TABLE users; --` and checks nothing happens.

**Q18. Why PostgreSQL over MongoDB?**
The data is strongly relational (user → trips → days → items, with reviews and hotels), and integrity matters:
cascades, RESTRICT on destinations in use, unique reviews. Postgres's JSONB still gives document-style storage
for plan snapshots.

**Q19. Why store budget, weather and route as JSON on the trip?**
They're snapshots of what the plan was based on. If catalogue prices change later, a saved plan still shows what
the user saw. Days and items are proper tables, because they're edited and queried individually.

**Q20. How is the itinerary made weather-aware when the trip is months away?**
Forecasts only cover 5 days. For later dates we use seasonal guidance: a monsoon month outside the destination's
best season counts as rain-likely. The UI marks each day as "forecast" or "seasonal".

**Q21. What does "Regenerate itinerary" change?**
It reruns planning with `variation + 1`. That adds small random tie-breaks to attraction scores, rotates which
days get which group of sights, alternates between the nearest restaurants and refreshes the weather. It's
deterministic for a given variation, so results are reproducible.

**Q22. How did you test the system?**
- **Backend** (85 tests, run on SQLite and on PostgreSQL in CI):
  - dataset integrity;
  - recommendation scenarios;
  - budget arithmetic;
  - the route optimiser against brute force;
  - itinerary rules;
  - the trip lifecycle and access control;
  - reviews and admin;
  - mocked external APIs;
  - security cases.
- **Frontend** (21 tests): validation, formatting, error messages and components.
- **CI** also checks lint and that migrations round-trip.

**Q23. How is it deployed?**
`docker compose up --build`. CI builds both images and pushes them to GHCR from `main`. For AWS: EC2 with Compose,
or ECS Fargate plus RDS, behind HTTPS, with only nginx exposed.

**Q24. What would you change for a million users?**
- Redis for caches and rate limits; several stateless API replicas behind a load balancer.
- A managed Postgres with read replicas.
- An IVF/HNSW FAISS index, with embeddings computed when catalogue rows change.
- A CDN for the frontend, and a task queue for heavy generation.

**Q25. What was the hardest bug?**
Silent scheduling drops. Full-day day trips (e.g. Pangong Lake, 12 hours) were assigned to a day but then failed
the 19:00 cut-off, leaving empty days. The fix had three parts:
- such days start at 07:00, and travel counts as part of the excursion;
- stops that don't fit carry over to the next day;
- any remaining drops are always reported to the user.
