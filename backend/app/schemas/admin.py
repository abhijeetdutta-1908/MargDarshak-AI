from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.preferences import DestinationType, HotelTier

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DestinationIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
    state: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    country: str = Field("India", max_length=80)
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=20, max_length=3000)]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    category: DestinationType
    tags: list[Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=2, max_length=30)]] = Field(max_length=20)
    best_seasons: list[int] = Field(min_length=1, max_length=12)
    ideal_min_days: int = Field(2, ge=1, le=30)
    ideal_max_days: int = Field(5, ge=1, le=30)
    average_daily_cost: int = Field(ge=0, le=1_000_000)
    average_hotel_cost: int = Field(ge=0, le=1_000_000)
    average_food_cost: int = Field(ge=0, le=1_000_000)
    average_transport_cost: int = Field(ge=0, le=1_000_000)
    popularity_score: float = Field(0.5, ge=0, le=1)
    image_url: str | None = Field(None, max_length=500)


class HotelIn(BaseModel):
    destination_id: int
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=160)]
    tier: HotelTier
    rating: float = Field(ge=1, le=5)
    price_per_night: int = Field(ge=0, le=1_000_000)
    address: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
    amenities: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]] = Field(default_factory=list, max_length=30)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    image_url: str | None = Field(None, max_length=500)


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    is_admin: bool
    trip_count: int = 0
    review_count: int = 0


class AdminUserUpdate(BaseModel):
    is_admin: bool


class ModerationUpdate(BaseModel):
    is_hidden: bool
