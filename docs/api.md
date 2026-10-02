# API reference

Interactive docs: **`/docs`** (Swagger) and **`/redoc`**. The machine-readable spec is at `/openapi.json`, which you
can import into Postman. All endpoints are under `/api`, and bodies are JSON.

**Auth.** `Authorization: Bearer <access_token>`, from register or login. Tokens last 24 hours. Logout or a password
change revokes all earlier tokens (via a token version stored on the user).

**Errors.** Every error has the shape `{"detail": "..."}`:

| Status | Meaning |
|--------|---------|
| 400 | Bad request (e.g. wrong current password) |
| 401 | Missing, invalid, expired or revoked token |
| 403 | Not allowed (not the owner, not an admin) |
| 404 | Not found (also returned for other users' trips, so their existence isn't revealed) |
| 409 | Conflict (email taken, duplicate review, destination in use) |
| 422 | Validation error (`detail` is a list of field errors) |
| 429 | Rate limited (`Retry-After` header) |
| 503 | Database or recommender unavailable |
| 500 | Generic message only; details go to the server log |

**Rate limits** (per client IP, sliding 60-second window): login 10, register 5, recommendations 30, trip
generation and regeneration 10.

## System
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | – | `{"status","database","version"}`; 503 if the database is down |
| GET | `/api/config` | – | Map provider, browser Maps key (if any), and whether live weather/places are on |

## Auth & users
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | – | `{name, email, password}` → `{access_token, token_type, user}` (201) |
| POST | `/api/auth/login` | – | `{email, password}` → token and user |
| GET | `/api/auth/me` | user | Current user |
| POST | `/api/auth/logout` | user | Revokes all tokens (204) |
| GET / PUT | `/api/users/me` | user | Read or update `{name, email, profile_image}` |
| POST | `/api/users/me/password` | user | `{current_password, new_password}` → a fresh token; other sessions are signed out |
| GET / PUT | `/api/preferences` | user | Saved travel preferences (types, interests, budget range, hotel tier, transport, food, travellers, starting location) |

Passwords need 8–72 characters and must mix letters with a number or symbol. Emails are lower-cased.

## Catalogue
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/destinations?category=&q=&page=&page_size=` | Most popular first, with pagination and a `cost_note` |
| GET | `/api/destinations/search?q=` | Matches name, state, description or tags (wildcards escaped) |
| GET | `/api/destinations/{id}` | Detail plus attraction, restaurant and hotel counts, average rating and review count |
| GET | `/api/hotels/{destination_id}?tier=&max_price=&preferred_tier=&nightly_budget=` | Cheapest first, or ranked with `score` and `reasons`. `source: "sample"` plus a note |
| GET | `/api/hotels/item/{hotel_id}` | One hotel |
| GET | `/api/places/{destination_id}?kind=&lat=&lng=` | Attractions, restaurants, shopping or activities sorted by distance. `source`: `google_places` or `seeded` |
| GET | `/api/weather/{destination_id}` | Current weather and 5-day forecast (`source: live`), or seasonal guidance (`source: fallback`, with the reason) |

## Recommendations
`POST /api/recommendations`:
```json
{ "budget": 20000, "duration": 4, "destination_type": "mountain", "interests": ["trekking","nature","photography"],
  "travel_date": "2026-11-10", "hotel_preference": "budget", "travelers": 2,
  "transport_preference": "public", "starting_location": "Delhi", "notes": "peaceful places", "top_k": 6 }
```
Response (illustrative values; run it in `/docs` for live output):
```json
{ "recommendations": [{ "destination_id": 6, "destination": "Manali", "state": "Himachal Pradesh", "category": "mountain",
    "score": 91.4, "confidence": 0.89,
    "reasons": ["Strong match for your mountain preference", "Suitable for trekking, nature, photography", "Fits your budget (est. ₹19,472 of ₹20,000)"],
    "warnings": [], "components": {"interest": 100, "semantic": 87.2, "type": 100, "budget": 100, "...": 0},
    "estimated_cost": {"minimum": 16155, "average": 19472, "maximum": 24898}, "best_seasons": [3,4,5,6,10,11,12],
    "latitude": 32.24, "longitude": 77.19 }],
  "engine": { "embedding": "sentence-transformers/all-MiniLM-L6-v2", "index": "faiss", "vectors": "prebuilt", "weights": {} },
  "query": "I want a mountain destination. I enjoy trekking, nature, photography.", "notes": [] }
```

## Routes
`POST /api/routes/optimize` with `{points: [{name, latitude, longitude}], start_index, return_to_start, transport}`
(2–25 points) returns `{order, stops, legs, total_distance_km, total_duration_minutes, initial_distance_km,
distance_source, note}`.

## Trips (auth required)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/trips/generate` | Recommendation body plus optional `destination_id`, `hotel_id` and `title`. Runs the whole pipeline and saves a draft (201). Returns the full trip |
| GET | `/api/trips?saved=&page=&page_size=` | The user's trips |
| GET | `/api/trips/{id}` | Full trip: destination, hotel, budget, weather, route, recommendations, explanations, days and items |
| PUT | `/api/trips/{id}` | `{title?, is_saved?, start_date?}` (day dates follow the start date) |
| DELETE | `/api/trips/{id}` | Delete (204) |
| POST | `/api/trips/{id}/duplicate` | Copy, including days and items (201) |
| POST / DELETE | `/api/trips/{id}/share` | Create or revoke a public link token |
| POST | `/api/trips/{id}/complete` | Mark as travelled and add to travel history |
| GET | `/api/trips/{id}/itinerary` | Just the days |
| POST | `/api/trips/{id}/itinerary/regenerate` | New plan: same destination and hotel, fresh weather, `variation + 1` |
| GET | `/api/shared/{token}` | **Public**, read-only trip |
| GET | `/api/dashboard` | Stats, upcoming and recent trips, favourites, recent recommendations, travel history |

## Reviews
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/destinations/{id}/reviews?page=` | – | `average_rating`, `review_count`, `distribution`, items |
| POST | `/api/destinations/{id}/reviews` | user | `{rating 1-5, comment ≤ 2000}`; one per user per destination (409 otherwise) |
| PUT / DELETE | `/api/reviews/{id}` | owner or admin | Edit or delete |
| GET | `/api/reviews/me` | user | My reviews |
| GET | `/api/reviews/recent?limit=` | – | Highly rated recent reviews (landing page) |

## Admin (admin token)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/stats` | Counts |
| POST / PUT / DELETE | `/api/admin/destinations[/{id}]` | Create, update, delete (409 if users have trips there). Invalidates the recommender cache |
| GET | `/api/admin/hotels?destination_id=` · POST / PUT / DELETE `/api/admin/hotels[/{id}]` | Hotel CRUD |
| GET | `/api/admin/users?q=` · PUT `/api/admin/users/{id}` `{is_admin}` | List users, grant or revoke admin (you can't demote yourself) |
| GET | `/api/admin/reviews?hidden=` · PUT `/api/admin/reviews/{id}` `{is_hidden}` · DELETE | Moderation |
