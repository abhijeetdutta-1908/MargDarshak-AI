# Database

PostgreSQL 16, accessed through SQLAlchemy 2 (typed `Mapped[...]` models in `backend/app/models/`).
Migrations are managed with Alembic (`database/migrations/`; run from `backend/`). List columns use **JSONB** on
PostgreSQL (plain JSON on SQLite in tests).

## Entity relationships

```
users 1──1 user_preferences
users 1──* saved_trips *──1 destinations
                 │  *──1 hotels (nullable, SET NULL)
                 └──* trip_days 1──* itinerary_items *──1 places (nullable, SET NULL)
users 1──* reviews *──1 destinations          (unique: one review per user per destination)
users 1──* bookings *──1 hotels               (reserved for future booking integration)
users 1──* travel_history *──1 destinations
destinations 1──* hotels
destinations 1──* places    (attraction | restaurant | shopping | activity)
```

## Tables

| Table | Key columns | Notes |
|-------|-------------|-------|
| `users` | `id`, `name`, `email` (unique, indexed, lower-cased), `password_hash` (bcrypt), `profile_image`, `is_admin`, `token_version`, timestamps | `token_version` is bumped on logout or password change to revoke JWTs |
| `user_preferences` | `user_id` (unique FK), `destination_types[]`, `interests[]`, `budget_min/max`, `hotel_preference`, `transport_preference`, `food_preference`, `travelers`, `starting_location` | Prefills the planner |
| `destinations` | `name` (indexed), `state`, `country`, `description`, `latitude/longitude`, `category` (indexed), `tags[]`, `best_seasons[]` (months), `ideal_min/max_days`, `average_daily/hotel/food/transport_cost`, `popularity_score`, `image_url` | Costs are INR estimates |
| `hotels` | `destination_id` (FK, indexed), `name`, `tier` (indexed), `rating`, `price_per_night`, `address`, `amenities[]`, `latitude/longitude`, `image_url` | Seeded rows are labelled samples |
| `places` | `destination_id` (FK, indexed), `name`, `kind` (indexed), `tags[]`, `description`, `is_indoor`, `rating`, `address`, `latitude/longitude`, `estimated_cost`, `duration_minutes` | Tags carry interest words plus `sunrise`, `evening`, `closed:M-N` |
| `reviews` | `user_id`, `destination_id` (both FK, indexed), `rating` (CHECK 1–5), `comment`, `is_hidden`, timestamps | UNIQUE(user_id, destination_id) |
| `saved_trips` | `user_id`, `destination_id` (RESTRICT), `hotel_id` (SET NULL), `title`, `start_date`, `duration_days`, `travelers`, `preferences{}`, `budget{}`, `weather{}`, `route{}`, `recommendations[]`, `explanations[]`, `unscheduled[]`, `variation`, `is_saved` (indexed), `is_completed`, `share_token` (unique), timestamps | JSON snapshots keep a saved plan reproducible even if catalogue prices change |
| `trip_days` | `trip_id` (FK, indexed), `day_number`, `date`, `title`, `weather_note`, `rain_likely`, `weather_source`, `total_distance_km`, `total_travel_minutes` | Ordered by `day_number` |
| `itinerary_items` | `trip_day_id` (FK, indexed), `destination_id`, `place_id`, `position`, `title`, `description`, `start_time`/`end_time` ("HH:MM"), `location`, `category`, `estimated_cost`, `latitude/longitude`, `duration_minutes`, `travel_minutes` | Ordered by `position` |
| `bookings` | `user_id`, `hotel_id`, `trip_id`, `check_in/out`, `guests`, `status` | Schema only; no payment flow in the MVP |
| `travel_history` | `user_id`, `destination_id`, `trip_id`, `visited_on`, `notes` | Written by "Mark as travelled" |

## Integrity and deletion rules

- Deleting a **user** cascades to their preferences, trips, reviews, bookings and history.
- Deleting a **destination** cascades to its hotels, places and reviews. It's **blocked** (RESTRICT, and a 409 from
  the admin API) while any trip references it.
- Deleting a **hotel** or **place** sets trip and itinerary references to NULL, so saved plans survive.
- Deleting a **trip** cascades to its days and items.

## Migrations

| Revision | Content |
|----------|---------|
| `51e19986ef05` | Initial schema: all 11 tables, FKs, indexes, constraints |
| `7cf9ca91e3c6` | Trip planning fields: explanations, unscheduled, variation, saved/completed flags, per-day weather and totals, per-item travel minutes |

```bash
cd backend
alembic upgrade head                                  # run automatically by the backend container
alembic revision --autogenerate -m "describe change"  # after editing models
```

CI checks `upgrade head` followed by `downgrade base` on every push.

## Seeding

`python database/seed.py` (also run on container start) loads `ml/datasets/*.csv`:
- 36 destinations;
- 293 places: 153 attractions, 68 restaurants, 46 activities and 26 shopping spots;
- 180 deterministic sample hotels.

It only inserts missing rows by default. `--update` reapplies the dataset values, and `--make-admin EMAIL` grants
admin access. Dataset integrity is tested in `backend/tests/test_dataset.py`.
