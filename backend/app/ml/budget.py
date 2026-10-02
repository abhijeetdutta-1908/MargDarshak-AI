"""Trip cost estimation. Pure functions over a destination's (estimated) cost profile."""

import math
from dataclasses import dataclass, field

TIER_HOTEL_FACTOR = {"budget": 0.4, "standard": 1.0, "premium": 2.0, "luxury": 4.0}
TIER_FOOD_FACTOR = {"budget": 0.8, "standard": 1.0, "premium": 1.4, "luxury": 2.0}
# Local transport, relative to the destination's per-person daily average.
PER_PERSON_MODES = {"public": 0.6, "bike": 0.75, "mixed": 1.0}
PER_VEHICLE_MODES = {"car": 1.4, "taxi": 1.7}  # x2.5 per vehicle (4 seats)
# Intercity round-trip INR per km: per person for shared modes, per vehicle for road modes.
INTERCITY_PER_KM = {"public": 1.2, "mixed": 1.8, "bike": 2.5, "car": 9.0, "taxi": 14.0}
FLIGHT_THRESHOLD_KM = 1000
MISC_RATE = 0.08

MODE_LABEL = {"public": "public transport", "mixed": "mixed transport", "bike": "bike", "car": "self-drive car", "taxi": "taxi"}


@dataclass
class CostProfile:
    name: str
    average_daily_cost: int
    average_hotel_cost: int
    average_food_cost: int
    average_transport_cost: int
    hotel_prices: dict[str, list[int]] = field(default_factory=dict)  # tier -> nightly prices


def _range(avg: float, lo: float, hi: float) -> dict[str, int]:
    return {"min": round(avg * lo), "average": round(avg), "max": round(avg * hi)}


def _inr(v: float) -> str:
    return f"₹{round(v):,}"


class BudgetCalculator:
    def __init__(
        self,
        profile: CostProfile,
        duration: int,
        travelers: int = 1,
        hotel_tier: str | None = None,
        transport: str | None = None,
        hotel_price: int | None = None,
        activity_cost_per_person: int | None = None,
        intercity_km: float | None = None,
        origin: str | None = None,
    ):
        self.p = profile
        self.duration = max(1, duration)
        self.nights = max(1, duration - 1)
        self.travelers = max(1, travelers)
        self.rooms = math.ceil(self.travelers / 2)
        self.tier = hotel_tier or "standard"
        self.transport = transport or "mixed"
        self.hotel_price = hotel_price
        self.activity_cost_per_person = activity_cost_per_person
        self.intercity_km = intercity_km
        self.origin = origin
        self.assumptions: list[str] = []

    def calculate_hotel_cost(self) -> dict[str, int]:
        units = self.nights * self.rooms
        if self.hotel_price:
            nightly = {"min": self.hotel_price, "average": self.hotel_price, "max": self.hotel_price}
            label = f"selected hotel at {_inr(self.hotel_price)}/night"
        elif prices := self.p.hotel_prices.get(self.tier):
            nightly = {"min": min(prices), "average": sum(prices) / len(prices), "max": max(prices)}
            label = f"{self.tier} hotels at ~{_inr(nightly['average'])}/night"
        else:
            avg = self.p.average_hotel_cost * TIER_HOTEL_FACTOR[self.tier]
            nightly = _range(avg, 0.8, 1.25)
            label = f"{self.tier} hotels at ~{_inr(avg)}/night (estimated)"
        self.assumptions.append(f"{self.nights} night(s) × {self.rooms} room(s), {label}")
        return {k: round(v * units) for k, v in nightly.items()}

    def calculate_food_cost(self) -> dict[str, int]:
        avg = self.p.average_food_cost * TIER_FOOD_FACTOR[self.tier] * self.travelers * self.duration
        return _range(avg, 0.85, 1.3)

    def calculate_transport_cost(self) -> dict[str, int]:
        base = self.p.average_transport_cost
        vehicles = math.ceil(self.travelers / 4)
        if self.transport in PER_VEHICLE_MODES:
            local = base * PER_VEHICLE_MODES[self.transport] * 2.5 * vehicles * self.duration
        else:
            local = base * PER_PERSON_MODES.get(self.transport, 1.0) * self.travelers * self.duration
        self.assumptions.append(f"Local travel by {MODE_LABEL.get(self.transport, self.transport)}")

        intercity = 0.0
        if self.intercity_km is None:
            self.assumptions.append("Travel to and from the destination not included (starting location unknown)")
        elif self.intercity_km < 15:
            self.assumptions.append("Starting at the destination, so no intercity travel")
        else:
            km = self.intercity_km
            if km > FLIGHT_THRESHOLD_KM and self.transport in ("public", "mixed", "taxi"):
                intercity = 2 * (2500 + 2.2 * km) * self.travelers
                how = "return flight (economy estimate)"
            elif self.transport in ("car", "taxi"):
                intercity = INTERCITY_PER_KM[self.transport] * km * 2 * vehicles
                how = f"return trip by {MODE_LABEL[self.transport]}"
            elif self.transport == "bike":
                intercity = INTERCITY_PER_KM["bike"] * km * 2 * math.ceil(self.travelers / 2)
                how = "return trip by bike"
            else:
                intercity = INTERCITY_PER_KM[self.transport] * km * 2 * self.travelers
                how = "return train/bus"
            self.assumptions.append(f"{self.origin or 'Origin'} → {self.p.name}: ~{round(km):,} km, {how}")
        local_r = _range(local, 0.85, 1.3)
        inter_r = _range(intercity, 0.8, 1.4)
        return {k: local_r[k] + inter_r[k] for k in local_r}

    def calculate_activity_cost(self) -> dict[str, int]:
        if self.activity_cost_per_person is not None:
            self.assumptions.append("Activities priced from the planned itinerary")
            return _range(self.activity_cost_per_person * self.travelers, 0.9, 1.25)
        per_day = max(
            200,
            self.p.average_daily_cost - self.p.average_hotel_cost / 2 - self.p.average_food_cost - self.p.average_transport_cost,
        )
        return _range(per_day * self.travelers * self.duration, 0.7, 1.4)

    def calculate_miscellaneous_cost(self, subtotal: dict[str, int]) -> dict[str, int]:
        return {k: round(v * MISC_RATE) for k, v in subtotal.items()}

    def calculate_total(self) -> dict:
        self.assumptions = []
        parts = {
            "accommodation": self.calculate_hotel_cost(),
            "transportation": self.calculate_transport_cost(),
            "food": self.calculate_food_cost(),
            "activities": self.calculate_activity_cost(),
        }
        subtotal = {k: sum(p[k] for p in parts.values()) for k in ("min", "average", "max")}
        parts["miscellaneous"] = self.calculate_miscellaneous_cost(subtotal)
        self.assumptions.append(f"Miscellaneous at {round(MISC_RATE * 100)}% (tips, shopping, contingencies)")
        totals = {k: sum(p[k] for p in parts.values()) for k in ("min", "average", "max")}
        return {
            "currency": "INR",
            "components": parts,
            "minimum": totals["min"],
            "average": totals["average"],
            "maximum": totals["max"],
            "per_person": round(totals["average"] / self.travelers),
            "travelers": self.travelers,
            "duration_days": self.duration,
            "assumptions": self.assumptions,
            "note": "Estimates from average costs in the destination dataset, not live prices.",
        }

    def calculate_minimum(self) -> int:
        return self.calculate_total()["minimum"]

    def calculate_average(self) -> int:
        return self.calculate_total()["average"]

    def calculate_maximum(self) -> int:
        return self.calculate_total()["maximum"]
