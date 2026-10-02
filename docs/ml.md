# ML & algorithms

All engines live in `backend/app/ml/` and are plain Python (no FastAPI imports), so they can be unit-tested and
run from the command line (`ml/recommendation_engine.py`).

| Module | Class / function | Role |
|--------|------------------|------|
| `semantic.py` | `Embedder`, `VectorIndex` | Text embeddings + vector search, with fallbacks |
| `recommendation.py` | `RecommendationEngine` | Hybrid destination ranking with explanations |
| `budget.py` | `BudgetCalculator` | Trip cost estimate (min / average / max) |
| `route.py` | `RouteOptimizer`, `estimate_matrix` | Visit order and travel times |
| `hotels.py` | `rank_hotels` | Hotel ranking |
| `itinerary.py` | `ItineraryGenerator` | Day-wise, weather-aware plan |
| `vocab.py` | `INTEREST_TAGS`, `TYPE_TAGS` | Maps planner vocabulary onto dataset tags |

---

## 1. Semantic layer (Sentence Transformers + FAISS)

**Destination text.** Each destination becomes one sentence:
`"{name}. A {category} destination. Known for {tags}. {description}"`.

**Query text.** The user's preferences become a sentence too:
`"I want a mountain destination. I enjoy trekking, nature, photography. <free-text notes>"`.

**Embeddings.** `sentence-transformers/all-MiniLM-L6-v2` produces a 384-dimensional vector, normalised to unit
length. The model is baked into the Docker image, and the container runs with `HF_HUB_OFFLINE=1`.

**Index.** `faiss.IndexFlatIP`. On unit vectors, the inner product equals cosine similarity. Flat (exact) search is
correct and instant for tens to thousands of items. Past about 100k items, switch to IVF or HNSW.

**Offline pipeline.**
1. `ml/create_embeddings.py` encodes the catalogue and writes `destination_embeddings.npy` plus a `meta.json`
   fingerprint (a SHA-256 of the backend name and all destination texts).
2. `ml/build_faiss_index.py` builds `destinations.faiss` and checks that every vector's nearest neighbour is itself.
3. At startup the engine loads these artifacts **only if the fingerprint matches** the current database
   catalogue. Otherwise it re-encodes, so stale artifacts can never give wrong results. `describe()` reports
   `vectors: prebuilt` or `built-at-startup`.

**Fallbacks** (chosen automatically and reported in the API's `engine` field):
- If Sentence Transformers or the model is unavailable, TF-IDF (scikit-learn, unigrams and bigrams, sublinear TF) is fitted on the destination texts.
- If faiss is missing, an exact NumPy dot-product search is used.

So the app never depends on an external LLM or a network download.

---

## 2. Recommendation engine

```
preferences ──► query text ──► embedding ──► FAISS top-k (k = max(3·top_k, 15))
                                             ∪ all destinations of the requested type(s)
            ──► per-candidate component scores ──► weighted sum ──► off-season penalty
            ──► budget filter ──► sort ──► reasons / warnings / confidence
```

### Component scores (each in [0, 1])

| Key | Weight | Formula |
|-----|--------|---------|
| `interest` | 0.20 | matched interests ÷ requested interests. An interest matches if its tag family (e.g. history → forts, ruins, unesco, museums…) intersects the destination's tags. 1.0 if none were requested |
| `semantic` | 0.10 | FAISS cosine similarity, min-max normalised across all destinations for this query |
| `type` | 0.15 | 1.0 if the category is requested; 0.6 if a requested type's tag family appears in the tags; else 0. 1.0 if no type was requested |
| `budget` | 0.20 | `r = estimated_average / budget`. Score is 1 if r ≤ 1, else `max(0, 1 − (r−1)/0.6)`, which reaches 0 at 60% over budget |
| `duration` | 0.10 | 1 inside [ideal_min, ideal_max]. Shorter: `1 − (min−d)/min`. Longer: `max(0.3, 1 − (d−max)/(1.5·max))` |
| `season` | 0.10 | 1 if the travel month is a best month, 0.5 if it's adjacent to one, else 0. 1.0 if no date was given |
| `activity` | 0.05 | share of interests supported by at least one actual place (attraction/activity) at the destination |
| `hotel` | 0.05 | 1 if a hotel of the preferred tier costs ≤ 45% of the budget per room-night, 0.5 if it costs more, 0.2 if that tier is missing |
| `popularity` | 0.05 | the dataset's `popularity_score` |

`score = 100 × Σ wᵢ·cᵢ`, and it's multiplied by **0.8 when `season = 0`** (off-season). Without that penalty a
perfect type match outweighs a 10%-weight season score, and the engine recommended Leh in January, when its passes
are closed. Weights are configurable (`RECOMMENDATION_WEIGHTS`) and re-normalised to sum to 1.

**Budget filter.** Candidates with `budget = 0` (over 60% above budget) are dropped, unless that would leave fewer
than `top_k` results.

**Confidence.** `confidence = score/100 × (0.5 + 0.1 × n)`, where n counts how many of these signals the user gave:
interests, destination type, date, hotel tier, notes or origin. A high score from sparse input gets lower
confidence.

**Explanations.** These are generated from the same numbers that produced the score:
- "Strong match for your mountain preference"
- "Fits your budget (est. ₹19,472 of ₹20,000)"
- "November is one of the best months to visit"

Warnings say what didn't match, for example "Likely over budget by ~₹4,722", "Best enjoyed over 3+ days", or
"July is off-season here (score reduced by 20%)". The API also returns every component on a 0–100 scale (the UI's
"Why this score?" panel).

**Origin.** A free-text starting city is matched against the catalogue plus 27 major Indian cities. If it's found, the
intercity cost is included in the estimate. If not, a note says travel costs are excluded.

### Validation (tests/test_recommendation.py)

| Preferences | Expected top results |
|-------------|----------------------|
| Mountain, trekking/nature/photography, ₹20k, 4 days, November | a mountain destination first; Manali, Darjeeling or Gangtok in the top 3 |
| Beach, nightlife/food, December | Goa in the top 3 |
| Wildlife and photography, February | Ranthambore, Jim Corbett or Kaziranga first |
| Religious, culture/history, January | top 3 ⊆ {Varanasi, Amritsar, Puri, Bodh Gaya} |
| Adventure, trekking, July vs January | Leh in the top 3 in July; never first in January, with an off-season warning |
| ₹3,000 for 5 days | still returns results, each with an "over budget" warning |
| `RUN_ST_TESTS=1` free text "snow-capped peaks, high passes, motorbike road trips" | Leh in the semantic top 3 |

---

## 3. Budget calculator

Inputs: the destination's cost profile, days `D`, travellers `T`, hotel tier, transport mode, and optionally the chosen
hotel's nightly price, the itinerary's activity cost and the intercity distance.

| Component | Average |
|-----------|---------|
| Accommodation | `nights (D−1, min 1) × rooms (⌈T/2⌉) × nightly` (chosen hotel, or the tier's average price) |
| Food | `avg_food × tier factor (0.8 / 1 / 1.4 / 2) × T × D` |
| Local transport | per person `avg_transport × mode factor × T × D` (public 0.6, bike 0.75, mixed 1.0); per vehicle for car (1.4) or taxi (1.7) × 2.5 × ⌈T/4⌉ × D |
| Intercity | round trip on 1.25 × straight-line km: train/bus ₹1.2/km/person; car ₹9/km/vehicle; taxi ₹14; bike ₹2.5. **Flights** (2 × (₹2,500 + ₹2.2/km) per person) above 1,000 km |
| Activities | the itinerary's entry fees, or `max(200, daily − hotel/2 − food − transport)` × T × D |
| Miscellaneous | 8% of the subtotal |

Each component carries its own min/max band (for example food 0.85–1.3×, or the tier's cheapest-to-dearest hotel),
and the totals are the sums. The result lists its **assumptions**, which the UI shows under "How this was calculated".

---

## 4. Route optimiser

1. **Distance matrix.** From the Google Routes API (`computeRouteMatrix`) when a key is set and there are ≤ 10 stops.
   Otherwise haversine × 1.3 road factor, with travel time at typical city speeds (walk 4.5 km/h for hops under
   800 m; public 16, mixed 22, car/taxi 26 km/h) plus 5 minutes per leg.
2. **Nearest neighbour** from the start (the hotel) gives a greedy tour.
3. **2-opt.** Reverse any segment `[i..j]` whose reversal shortens the route, and repeat until none does.
4. **Or-opt.** Move any run of 1–3 stops (in either direction) to the best position.
5. Alternate 3 and 4 until neither improves. The start stays fixed; the route can be open or return to the start.

**Measured quality** (600 random instances, 5–8 stops, against brute force):

| Method | Mean gap to optimal | Worst gap | Optimal |
|--------|--------------------|-----------|---------|
| Nearest neighbour only | 5.48% | 43.5% | – |
| NN + 2-opt + Or-opt | **0.11%** | 8.9% | **96%** |

`POST /api/routes/optimize` returns the order, legs, totals and the distance of the original order for comparison.

---

## 5. Hotel ranking

`score = 100 × (0.35·budget + 0.25·rating + 0.20·tier + 0.20·distance)`:
- **Budget:** 1 if the price is ≤ the nightly budget (45% of the trip budget ÷ nights ÷ rooms), falling to 0 at 75% over.
- **Rating:** (rating − 3) / 2.
- **Tier:** 1 for an exact match, 0.5 for one tier away.
- **Distance:** 1 − km to the centroid of the destination's attractions ÷ 15.

Reasons such as "Within your nightly budget", "Highly rated (4.6)" and "1.2 km from your planned sights" come from
the same terms.

---

## 6. Itinerary generator

1. **Day slots.**
   - Day 1 starts sightseeing at 11:00, after arrival at 09:00 and check-in.
   - Middle days run 09:00–19:00.
   - The last day runs 09:45–13:00, then departure.
   - A one-day trip runs 08:45–18:30.
2. **Seasonal closures.** Places tagged `closed:M-N` are dropped when the trip dates fall in those months (for
   example Rohtang Pass `closed:11-4`, or the Eravikulam calving season `closed:2-3`). The plan explains this.
3. **Selection.** Each attraction, activity or shopping place is scored
   `0.6 × interest match + 0.4 × (rating − 3)/2`. Shopping is halved unless "shopping" is an interest. Places are
   picked greedily until the trip's time budget is full (duration + about 25 minutes of travel each). Full-day
   excursions (5 hours or more) are limited to the number of dry middle days.
4. **Weather.**
   - Each day's outlook comes from the OpenWeather forecast when the date is within 5 days. Otherwise it's seasonal:
     a monsoon month (June–September) outside the destination's best season counts as rain-likely.
   - If rainy days need more indoor time than the picks provide, the lowest-scoring outdoor picks are swapped for
     indoor alternatives.
5. **Grouping.**
   - Excursions go first, onto dry middle days.
   - The rest are put in route order from the hotel. Rainy days are filled with indoor places first, dry days with
     outdoor places, then whatever is left.
   - "Regenerate" rotates which days get which group and alternates restaurant choices.
6. **Daily route.** RouteOptimizer runs from the hotel and back. Then time-of-day rules apply:
   - sunrise spots go first, with a 05:15 start and breakfast afterwards, and never on arrival day;
   - evening and sunset spots go last, starting no earlier than 17:30.
7. **Time slots.**
   - Walk the route, adding travel time per leg.
   - Insert lunch at the restaurant nearest your position between about 12:45 and 14:30. Vegetarian preference uses
     veg-tagged places, and the least-used restaurant is preferred.
   - Insert dinner from 19:30, then the return to the hotel.
   - Gaps of 90 minutes or more become labelled "Free time".
   - Full-day excursions include travel in their duration, start at 07:00 after an early breakfast, and skip
     separate lunch.
8. **Carry-over.** A stop that doesn't fit its day is retried on the following days. Only then is it listed as
   "Not enough time for: …".
9. **Output.**
   - Per day: dated items with start/end times, location, category, cost, coordinates, duration and travel
     minutes, plus distance and travel totals.
   - Per trip: the explanations shown to the user, the unscheduled list, and activity cost per person (fed into
     the budget).

Validated in `tests/test_itinerary.py`:
- timelines are ordered and complete for 6 destinations;
- the rainy day gets indoor places, and when there are no indoor options it is explained honestly;
- vegetarian restaurants are chosen for a veg preference;
- single-day trips work;
- excursion days have no separate lunch;
- time-of-day rules hold (aarti at 17:30 or later, sunrise ride before 07:00 followed by breakfast);
- closures apply in November but not in June;
- regenerate gives a different plan, deterministically per variation.
