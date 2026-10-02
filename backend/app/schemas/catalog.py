from pydantic import BaseModel, ConfigDict

COST_NOTE = "Costs are estimated averages in INR (2026) for planning, not live prices."
HOTEL_NOTE = "Sample hotel listings generated for demonstration — not real properties, live prices or availability."


class DestinationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str
    country: str
    description: str
    latitude: float
    longitude: float
    category: str
    tags: list[str]
    best_seasons: list[int]
    ideal_min_days: int
    ideal_max_days: int
    average_daily_cost: int
    average_hotel_cost: int
    average_food_cost: int
    average_transport_cost: int
    popularity_score: float
    image_url: str | None


class DestinationDetail(DestinationOut):
    attraction_count: int
    restaurant_count: int
    hotel_count: int
    cost_note: str = COST_NOTE


class DestinationPage(BaseModel):
    items: list[DestinationOut]
    total: int
    page: int
    page_size: int
    cost_note: str = COST_NOTE


class HotelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_id: int
    name: str
    tier: str
    rating: float
    price_per_night: int
    address: str
    amenities: list[str]
    latitude: float
    longitude: float
    image_url: str | None


class HotelList(BaseModel):
    source: str = "sample"
    note: str = HOTEL_NOTE
    items: list[HotelOut]
