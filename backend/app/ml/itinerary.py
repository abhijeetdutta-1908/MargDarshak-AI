"""Day-wise itinerary generation.

1. select_attractions()   score places by interests + rating, fill the trip's time budget
2. consider_weather()     on rainy days swap outdoor picks for indoor alternatives
3. group_by_location()    route-order the picks from the hotel, then fill days
                          (indoor first on rainy days, full-day excursions on dry days)
4. optimize_daily_route() nearest-neighbour + 2-opt + Or-opt loop from the hotel each day
5. assign_time_slots()    timeline with travel times, lunch/dinner near where you are
6. estimate_activity_cost()
7. generate_day_plan()    one day's items; generate() runs the whole pipeline
"""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.ml.route import RouteOptimizer, estimate_matrix
from app.ml.vocab import interest_matches

FULL_DAY_MINUTES = 300
DAY_END = 19 * 60  # last activity should end by 19:00
LUNCH_FROM, LUNCH_LATEST = 12 * 60 + 45, 14 * 60 + 30
EVENING_TAGS = {"sunset", "evening", "nightlife"}
VEG_TAGS = {"veg", "sweets", "south-indian", "lassi", "sadya"}  # restaurants tagged this way are vegetarian-friendly


@dataclass
class PlaceItem:
    id: int | None
    name: str
    kind: str
    tags: set[str]
    is_indoor: bool
    rating: float
    estimated_cost: int
    duration_minutes: int
    latitude: float
    longitude: float
    description: str | None = None
    address: str | None = None

    @property
    def outdoor(self) -> bool:
        return not self.is_indoor

    @property
    def full_day(self) -> bool:
        return self.duration_minutes >= FULL_DAY_MINUTES


@dataclass
class HotelStay:
    id: int | None
    name: str
    latitude: float
    longitude: float


@dataclass
class DayWeather:
    rain_likely: bool = False
    summary: str = "No forecast"
    source: str = "seasonal"


@dataclass
class DaySlot:
    number: int
    date: date | None
    weather: DayWeather
    start: int  # minutes since midnight when sightseeing can begin
    end: int  # latest activity end
    kind: str  # first | middle | last | single
    places: list[PlaceItem] = field(default_factory=list)

    @property
    def capacity(self) -> int:
        return self.end - self.start - (0 if self.kind == "last" else 60)  # lunch is after 13:00 on the last day

    def used(self) -> int:
        return sum(p.duration_minutes + 25 for p in self.places)  # + rough travel per stop


def closed_months(tags: set[str]) -> set[int]:
    """Parse seasonal closure tags like "closed:11-4" (Nov through Apr, wrapping the year)."""
    months: set[int] = set()
    for tag in tags:
        if tag.startswith("closed:"):
            a, _, b = tag[7:].partition("-")
            start, end = int(a), int(b or a)
            m = start
            while True:
                months.add(m)
                if m == end:
                    break
                m = m % 12 + 1
    return months


def hhmm(m: int) -> str:
    m = max(0, min(m, 23 * 60 + 59))
    return f"{m // 60:02d}:{m % 60:02d}"


class ItineraryGenerator:
    def __init__(self, destination: str, center: tuple[float, float], duration: int, places: list[PlaceItem],
                 hotel: HotelStay | None = None, interests: list[str] | None = None, travelers: int = 1,
                 start_date: date | None = None, weather: list[DayWeather] | None = None,
                 food_preference: str | None = None, transport: str | None = None, variation: int = 0):
        self.destination = destination
        self.duration = max(1, duration)
        self.interests = interests or []
        self.travelers = max(1, travelers)
        self.start_date = start_date
        self.food_preference = food_preference
        self.transport = transport or "mixed"
        self.rng = random.Random(variation)
        self.variation = variation
        self.hotel = hotel or HotelStay(None, f"Stay in {destination}", *center)
        self.attractions = [p for p in places if p.kind in ("attraction", "activity", "shopping")]
        self.closed: list[str] = []
        if start_date:  # drop places that are seasonally closed on the trip dates
            trip_months = {(start_date + timedelta(days=i)).month for i in range(self.duration)}
            self.closed = [p.name for p in self.attractions if closed_months(p.tags) & trip_months]
            self.attractions = [p for p in self.attractions if p.name not in self.closed]
        self.restaurants = [p for p in places if p.kind == "restaurant"]
        weather = weather or []
        self.days = [self._slot(i + 1, weather[i] if i < len(weather) else DayWeather()) for i in range(self.duration)]
        self.explanations: list[str] = []
        self.unscheduled: list[PlaceItem] = []
        self._used_restaurants: dict[str, int] = {}
        self._swaps: list[str] = []
        self._dropped: list[PlaceItem] = []

    def _slot(self, n: int, w: DayWeather) -> DaySlot:
        d = self.start_date + timedelta(days=n - 1) if self.start_date else None
        if self.duration == 1:
            return DaySlot(n, d, w, 8 * 60 + 45, 18 * 60 + 30, "single")
        if n == 1:
            return DaySlot(n, d, w, 11 * 60, DAY_END, "first")
        if n == self.duration:
            return DaySlot(n, d, w, 9 * 60 + 45, 13 * 60, "last")
        return DaySlot(n, d, w, 9 * 60, DAY_END, "middle")

    # ---- 1. selection ----------------------------------------------------------------------
    def _score(self, p: PlaceItem) -> float:
        tags = p.tags | {p.kind}
        interest = (sum(interest_matches(i, tags) for i in self.interests) / len(self.interests)) if self.interests else 0.5
        s = 0.6 * interest + 0.4 * max(0.0, (p.rating - 3.0) / 2.0)
        if p.kind == "shopping" and "shopping" not in self.interests:
            s *= 0.5
        if self.variation:
            s += self.rng.uniform(-0.12, 0.12)  # regenerate => different but still sensible picks
        return s

    def select_attractions(self) -> list[PlaceItem]:
        budget = sum(d.capacity for d in self.days)
        dry_full_days = sum(1 for d in self.days if d.kind == "middle" and not d.weather.rain_likely)
        chosen, used, full_days = [], 0, 0
        for p in sorted(self.attractions, key=lambda p: (-self._score(p), p.name)):
            if p.full_day:
                if full_days >= max(dry_full_days, 0) or self._score(p) < 0.45:
                    continue
                full_days += 1
            cost = p.duration_minutes + 25
            if used + cost <= budget:
                chosen.append(p)
                used += cost
        return chosen

    # ---- 2. weather --------------------------------------------------------------------------
    def consider_weather(self, chosen: list[PlaceItem]) -> list[PlaceItem]:
        rainy = [d for d in self.days if d.weather.rain_likely]
        if not rainy:
            return chosen
        indoor_needed = sum(d.capacity for d in rainy)
        indoor_have = sum(p.duration_minutes + 25 for p in chosen if p.is_indoor)
        spare = [p for p in sorted(self.attractions, key=lambda p: -self._score(p))
                 if p.is_indoor and p not in chosen and not p.full_day]
        swaps = []
        while indoor_have < indoor_needed and spare:
            outdoor = [p for p in chosen if p.outdoor and not p.full_day]
            if not outdoor:
                break
            drop = min(outdoor, key=self._score)
            add = spare.pop(0)
            chosen = [add if p is drop else p for p in chosen]
            indoor_have += add.duration_minutes + 25
            swaps.append(f"{add.name} instead of {drop.name}")
        self._swaps = swaps
        return chosen

    def _explain_weather(self) -> None:
        rainy = [d for d in self.days if d.weather.rain_likely]
        if not rainy:
            return
        days = ", ".join(str(d.number) for d in rainy)
        indoor = [p.name for d in rainy for p in d.places if p.is_indoor]
        outdoor_dry = [p.name for d in self.days if not d.weather.rain_likely for p in d.places if p.outdoor]
        if indoor:
            msg = f"Rain is likely on day {days}, so indoor places ({', '.join(indoor[:3])}) are scheduled then"
            if outdoor_dry:
                msg += f" and outdoor plans like {outdoor_dry[0]} moved to drier days"
            still_out = [p.name for d in rainy for p in d.places if p.outdoor]
            if still_out:
                msg += f"; {still_out[0]} is still on a rainy day, so keep it flexible"
        else:
            msg = f"Rain is likely on day {days} and {self.destination} has few indoor sights; keep that day flexible"
        if self._swaps:
            msg += f" (swapped in {'; '.join(self._swaps)})"
        self.explanations.append(msg + ".")

    # ---- 3. grouping ---------------------------------------------------------------------------
    def _route(self, stops: list[PlaceItem]) -> list[PlaceItem]:
        if len(stops) < 2:
            return stops
        pts = [(self.hotel.latitude, self.hotel.longitude)] + [(p.latitude, p.longitude) for p in stops]
        km, minutes = estimate_matrix(pts, self.transport)
        order = RouteOptimizer(km, minutes, 0, return_to_start=True).optimize()["order"]
        return [stops[i - 1] for i in order[1:]]

    def group_by_location(self, chosen: list[PlaceItem]) -> None:
        excursions = [p for p in chosen if p.full_day]
        regular = self._route([p for p in chosen if not p.full_day])

        for p in excursions:
            dry = [d for d in self.days if d.kind == "middle" and not d.places and not d.weather.rain_likely]
            slot = (dry or [d for d in self.days if d.kind == "middle" and not d.places] or [None])[0]
            if slot is None:
                self.unscheduled.append(p)
            else:
                slot.places.append(p)

        def fill(days: list[DaySlot], pool: list[PlaceItem]) -> list[PlaceItem]:
            left = []
            for p in pool:
                slot = next((d for d in days if d.used() + p.duration_minutes + 25 <= d.capacity
                             and not any(x.full_day for x in d.places)), None)
                (slot.places.append(p) if slot else left.append(p))
            return left

        def rotate(xs: list) -> list:  # "regenerate" redistributes sights across days
            k = self.variation % len(xs) if xs else 0
            return xs[k:] + xs[:k]

        rainy = rotate([d for d in self.days if d.weather.rain_likely])
        dry = rotate([d for d in self.days if not d.weather.rain_likely])
        indoor = [p for p in regular if p.is_indoor]
        outdoor = [p for p in regular if p.outdoor]
        left = fill(rainy, indoor)  # rainy days take indoor places first
        left = fill(dry, outdoor + left)
        if left and rainy:
            left = fill(rainy, left)
        self.unscheduled += left

    # ---- 4. daily routes -------------------------------------------------------------------------
    def optimize_daily_route(self, day: DaySlot) -> None:
        """Shortest route from the hotel, then time-of-day rules: sunrise spots first, evening spots last."""
        day.places = self._route(day.places)
        if day.kind == "first":  # you can't catch a sunrise on arrival day
            self._dropped += [p for p in day.places if "sunrise" in p.tags]
            day.places = [p for p in day.places if "sunrise" not in p.tags]
        sunrise = [p for p in day.places if "sunrise" in p.tags][:1]
        evening = [p for p in day.places if p.tags & EVENING_TAGS and p not in sunrise]
        if day.kind == "last":
            evening = []  # leaving in the afternoon
        rest = [p for p in day.places if p not in sunrise and p not in evening]
        day.places = sunrise + rest + evening

    # ---- 5. restaurants + time slots -----------------------------------------------------------
    def select_restaurants(self, near: tuple[float, float]) -> PlaceItem | None:
        pool = self.restaurants
        if self.food_preference == "veg":
            veg = [r for r in pool if r.tags & VEG_TAGS]
            if veg:
                pool = veg
        if not pool:
            return None
        ranked = sorted(pool, key=lambda r: (self._used_restaurants.get(r.name, 0),
                                             (r.latitude - near[0]) ** 2 + (r.longitude - near[1]) ** 2, r.name))
        least = self._used_restaurants.get(ranked[0].name, 0)
        options = [r for r in ranked if self._used_restaurants.get(r.name, 0) == least][:2]
        pick = options[self.variation % len(options)]
        self._used_restaurants[pick.name] = self._used_restaurants.get(pick.name, 0) + 1
        return pick

    def _item(self, title, start, minutes, category, *, place: PlaceItem | None = None, description=None,
              cost=0, travel=0, location=None):
        lat, lng = (place.latitude, place.longitude) if place else (self.hotel.latitude, self.hotel.longitude)
        return {
            "title": title,
            "description": description if description is not None else (place.description if place else None),
            "start_time": hhmm(start),
            "end_time": hhmm(start + minutes),
            "location": location or (place.address or place.name if place else self.hotel.name),
            "category": category,
            "estimated_cost": cost,
            "latitude": lat,
            "longitude": lng,
            "duration_minutes": minutes,
            "place_id": place.id if place else None,
            "travel_minutes": round(travel),
        }

    def _meal(self, label: str, t: int, near: tuple[float, float], prev: tuple[float, float]):
        r = self.select_restaurants(near)
        if r is None:
            return self._item(label, t, 60, "meal", description="Local restaurant near you", location=self.destination), (t + 60), prev
        travel = estimate_matrix([prev, (r.latitude, r.longitude)], self.transport)[1][0][1]
        start = t + round(travel)
        item = self._item(f"{label} at {r.name}", start, 60, "meal", place=r,
                          cost=r.estimated_cost * self.travelers, travel=travel)
        return item, start + 60, (r.latitude, r.longitude)

    def _free_time(self, items: list[dict], start: int, until: int) -> None:
        if until - start >= 90:
            items.append(self._item("Free time", start, until - start, "rest",
                                    description="Rest, explore the neighbourhood or revisit a favourite spot",
                                    location=self.destination))

    def assign_time_slots(self, day: DaySlot) -> list[dict]:
        hotel = (self.hotel.latitude, self.hotel.longitude)
        items = []
        if day.kind in ("first", "single"):
            items.append(self._item(f"Arrive in {self.destination}", day.start - (120 if day.kind == "first" else 45),
                                    60 if day.kind == "first" else 30, "arrival", description="Travel in and get oriented"))
            if day.kind == "first":
                items.append(self._item(f"Check in at {self.hotel.name}", day.start - 60, 45, "check-in"))
        elif day.places and "sunrise" in day.places[0].tags:
            pass  # breakfast is added after the sunrise stop below
        elif any(p.full_day for p in day.places):
            items.append(self._item("Early breakfast", 6 * 60 + 15, 30, "meal", location=self.hotel.name,
                                    description="Early start for a full-day trip"))
        else:
            items.append(self._item("Breakfast", 8 * 60, 45, "meal", location=self.hotel.name))
            if day.kind == "last":
                items.append(self._item(f"Check out of {self.hotel.name}", 9 * 60, 30, "check-out"))

        t, pos, lunch_done = day.start, hotel, False
        early_sunrise = day.kind != "first" and bool(day.places) and "sunrise" in day.places[0].tags
        if early_sunrise:
            t = 5 * 60 + 15
        elif day.kind == "middle" and any(p.full_day for p in day.places):
            t = 7 * 60
        for p in day.places:
            here = (p.latitude, p.longitude)
            # Day-trip durations in the dataset already include the drive there and back.
            travel = 0 if p.full_day else estimate_matrix([pos, here], self.transport)[1][0][1]
            if not p.full_day and not lunch_done and t + travel + min(p.duration_minutes, 90) > LUNCH_FROM + 30 and t <= LUNCH_LATEST:
                meal, t, pos = self._meal("Lunch", max(t, LUNCH_FROM - 15), pos, pos)
                items.append(meal)
                lunch_done = True
                travel = estimate_matrix([pos, here], self.transport)[1][0][1]
            start = t + round(travel)
            limit = 20 * 60 + 30 if p.full_day else day.end + (30 if "sunset" in p.tags else 0)
            if start + p.duration_minutes > limit:
                self._dropped.append(p)  # retried on the next day by generate()
                continue
            category = "activity" if p.kind == "activity" else p.kind
            desc = p.description
            if p.full_day:
                lunch_done = True  # long excursions: eat on the way
                desc = f"{desc or ''} Full-day trip including travel; carry water and plan lunch en route.".strip()
            if p.tags & EVENING_TAGS and day.kind != "last":
                start = max(start, 17 * 60 + 30)  # evening events/sunsets happen late in the day
            items.append(self._item(p.name, start, p.duration_minutes, category, place=p, description=desc,
                                    cost=p.estimated_cost * self.travelers, travel=travel))
            t, pos = start + p.duration_minutes, (hotel if p.full_day else here)
            if early_sunrise and p is day.places[0]:
                back = estimate_matrix([pos, hotel], self.transport)[1][0][1]
                items.append(self._item("Breakfast", t + round(back), 45, "meal", location=self.hotel.name, travel=back))
                t, pos = t + round(back) + 45, hotel
                if day.kind == "last":
                    items.append(self._item(f"Check out of {self.hotel.name}", t, 30, "check-out"))
                    t += 30

        if not lunch_done:
            self._free_time(items, t, LUNCH_FROM)
            meal, t, pos = self._meal("Lunch", max(t, LUNCH_FROM), pos, pos)
            items.append(meal)
        if day.kind == "last":
            back = estimate_matrix([pos, hotel], self.transport)[1][0][1]
            items.append(self._item("Depart", max(t + round(back), 14 * 60 + 30), 30, "departure",
                                    description="Collect bags and head home", travel=back))
            return items
        self._free_time(items, t, 19 * 60 + 15)
        meal, t, pos = self._meal("Dinner", max(t, 19 * 60 + 30), pos, pos)
        items.append(meal)
        back = estimate_matrix([pos, hotel], self.transport)[1][0][1]
        if day.kind == "single":
            items.append(self._item("Depart", t + round(back), 30, "departure", description="Head home", travel=back))
        else:
            items.append(self._item(f"Return to {self.hotel.name}", t + round(back), 15, "travel", travel=back))
        return items

    # ---- 6/7. costs + output ---------------------------------------------------------------------
    @staticmethod
    def estimate_activity_cost(items: list[dict]) -> int:
        return sum(i["estimated_cost"] for i in items if i["category"] in ("attraction", "activity", "shopping"))

    def generate_day_plan(self, day: DaySlot) -> dict:
        self.optimize_daily_route(day)
        items = self.assign_time_slots(day)
        stops = [(i["latitude"], i["longitude"]) for i in items]
        km = sum(estimate_matrix([a, b], self.transport)[0][0][1] for a, b in zip(stops, stops[1:], strict=False))
        main = [p.name for p in day.places[:2]]
        return {
            "day_number": day.number,
            "date": day.date.isoformat() if day.date else None,
            "title": " & ".join(main) if main else ("Arrival and settling in" if day.kind == "first" else "Leisure day"),
            "weather": {"rain_likely": day.weather.rain_likely, "summary": day.weather.summary, "source": day.weather.source},
            "items": items,
            "total_distance_km": round(km, 1),
            "total_travel_minutes": round(sum(i["travel_minutes"] for i in items)),
            "activity_cost": self.estimate_activity_cost(items),
            "meal_cost": sum(i["estimated_cost"] for i in items if i["category"] == "meal"),
        }

    def generate(self) -> dict:
        chosen = self.consider_weather(self.select_attractions())
        self.group_by_location(chosen)
        self._explain_weather()
        days = []
        for d in self.days:
            carry, self._dropped = self._dropped, []
            if any(p.full_day for p in d.places):
                days.append(self.generate_day_plan(d))
                self._dropped = carry + self._dropped  # excursion day: pass leftovers on
                continue
            room = d.capacity - d.used()
            fits = [p for p in carry if not p.full_day and (room := room - p.duration_minutes - 25) >= 0]
            d.places += fits
            days.append(self.generate_day_plan(d))
            self._dropped = [p for p in carry if p not in fits] + self._dropped  # try again tomorrow
        self.unscheduled += self._dropped
        if self.closed:
            self.explanations.append(f"Left out because it's usually closed on your dates: {', '.join(self.closed)}.")
        if self.unscheduled:
            names = list(dict.fromkeys(p.name for p in self.unscheduled))
            self.explanations.append(f"Not enough time for: {', '.join(names)}. Consider an extra day.")
        if self.food_preference == "veg" and not any(r.tags & VEG_TAGS for r in self.restaurants):
            self.explanations.append("No restaurants here are tagged vegetarian; check menus locally.")
        total_cost = sum(d["activity_cost"] for d in days)
        return {
            "days": days,
            "explanations": self.explanations,
            "unscheduled": list(dict.fromkeys(p.name for p in self.unscheduled)),
            "activity_cost_per_person": round(total_cost / self.travelers),
            "route": {
                "total_distance_km": round(sum(d["total_distance_km"] for d in days), 1),
                "total_travel_minutes": sum(d["total_travel_minutes"] for d in days),
                "source": "estimate",
                "note": "Travel times estimated from coordinates and typical city speeds.",
            },
        }
