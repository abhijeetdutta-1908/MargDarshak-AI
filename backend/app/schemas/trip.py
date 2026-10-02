from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.catalog import HotelOut
from app.schemas.recommendation import RecommendationRequest


class TripGenerateRequest(RecommendationRequest):
    destination_id: int | None = Field(None, description="Plan for this destination; default is the top recommendation")
    hotel_id: int | None = Field(None, description="Use this hotel; default is the best-ranked one")
    title: str | None = Field(None, max_length=160)


class ItineraryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    title: str
    description: str | None
    start_time: str
    end_time: str
    location: str | None
    category: str
    estimated_cost: int
    latitude: float | None
    longitude: float | None
    duration_minutes: int
    travel_minutes: int
    place_id: int | None


class TripDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day_number: int
    date: date | None
    title: str | None
    weather_note: str | None
    rain_likely: bool
    weather_source: str | None
    total_distance_km: float
    total_travel_minutes: int
    items: list[ItineraryItemOut]


class TripDestination(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str
    category: str
    description: str
    latitude: float
    longitude: float
    tags: list[str]
    best_seasons: list[int]
    image_url: str | None


class TripSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    destination: TripDestination
    start_date: date | None
    duration_days: int
    travelers: int
    budget: dict
    is_saved: bool
    is_completed: bool
    share_token: str | None
    created_at: datetime
    updated_at: datetime


class TripOut(TripSummary):
    hotel: HotelOut | None
    preferences: dict
    weather: dict
    route: dict
    recommendations: list
    explanations: list[str]
    unscheduled: list[str]
    variation: int
    days: list[TripDayOut]


class TripPage(BaseModel):
    items: list[TripSummary]
    total: int
    page: int
    page_size: int


class TripUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=160)
    is_saved: bool | None = None
    start_date: date | None = None


class ShareResponse(BaseModel):
    share_token: str
    path: str
