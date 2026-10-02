from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DestinationType = Literal[
    "beach", "mountain", "historical", "religious", "adventure", "wildlife", "city", "nature", "cultural"
]
Interest = Literal[
    "trekking", "photography", "food", "shopping", "adventure", "nature",
    "history", "culture", "nightlife", "relaxation", "wildlife",
]
HotelTier = Literal["budget", "standard", "premium", "luxury"]
Transport = Literal["public", "car", "bike", "taxi", "mixed"]
FoodPreference = Literal["veg", "non-veg", "both"]


class PreferencesIn(BaseModel):
    destination_types: list[DestinationType] = Field(default_factory=list, max_length=9)
    interests: list[Interest] = Field(default_factory=list, max_length=11)
    budget_min: int | None = Field(None, ge=0, le=10_000_000)
    budget_max: int | None = Field(None, ge=0, le=10_000_000)
    hotel_preference: HotelTier | None = None
    transport_preference: Transport | None = None
    food_preference: FoodPreference | None = None
    travelers: int | None = Field(None, ge=1, le=50)
    starting_location: str | None = Field(None, max_length=120)

    @model_validator(mode="after")
    def _budget_range(self):
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValueError("budget_min cannot exceed budget_max")
        return self


class PreferencesOut(PreferencesIn):
    model_config = ConfigDict(from_attributes=True)
