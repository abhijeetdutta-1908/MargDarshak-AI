# Datasets

Hand-authored for this project. Nothing is scraped from third-party sites.

| File | Rows | What |
|------|------|------|
| `destinations.csv` | 36 | Indian destinations: category, tags, best months, ideal trip length, cost profile, popularity |
| `places.csv` | 293 | Attractions (153), restaurants (68), activities (46) and shopping (26), linked by `destination` name |
| hotels | 180 | **Generated** by `database/seed.py`: 5 per destination (budget, 2× standard, premium, luxury) |

## How to read the numbers

- **Coordinates** are approximate (city centre or landmark), good to within roughly 1 km. Use them for maps and
  route distances, not navigation.
- **Costs are planning estimates in INR (2026)**, not quoted prices:
  - `average_hotel_cost`: one standard room per night
  - `average_food_cost` / `average_transport_cost`: per person per day (local transport only)
  - `average_daily_cost`: typical per-person all-in day: half a room, food, local transport and activities
  - `estimated_cost` (places): per-person entry fee or average meal cost
- **Ratings** on places are indicative, not live review scores.
- **Hotels are fictional sample listings.** Names, prices and amenities are generated from the destination's cost
  profile with a fixed seed, so every run gives the same data. The API returns them with `source: "sample"` and a
  note saying so.
- Restaurant rows are either long-established, well-known places or descriptive entries for a kind of local
  eatery (e.g. "Kachori Gali street food"). Opening hours and current status are not tracked.

`best_seasons` lists month numbers (1 = January). `tags` are pipe-separated and use the same interest vocabulary
as the planner (`trekking`, `photography`, `food`, …), plus descriptive tags.

Validated by `backend/tests/test_dataset.py`. Among other checks, every place must lie within 160 km of its
destination, and daily costs must cover the room, food and transport components.
