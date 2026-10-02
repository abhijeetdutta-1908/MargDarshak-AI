from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.schemas.preferences import DestinationType, FoodPreference, HotelTier, Interest, Transport


class RecommendationRequest(BaseModel):
    budget: int = Field(gt=0, le=10_000_000, description="Total trip budget in INR for the whole group")
    duration: int = Field(ge=1, le=30, description="Trip length in days")
    travelers: int = Field(1, ge=1, le=50)
    destination_type: DestinationType | None = None
    destination_types: list[DestinationType] = Field(default_factory=list, max_length=9)
    interests: list[Interest] = Field(default_factory=list, max_length=11)
    travel_date: date | None = None
    hotel_preference: HotelTier | None = None
    transport_preference: Transport | None = None
    food_preference: FoodPreference | None = None
    starting_location: str | None = Field(None, max_length=120)
    notes: str | None = Field(None, max_length=300, description="Free text, e.g. 'peaceful places, photography'")
    top_k: int = Field(6, ge=1, le=20)

    model_config = {
        "json_schema_extra": {
            "example": {
                "budget": 20000, "duration": 4, "destination_type": "mountain",
                "interests": ["trekking", "nature", "photography"], "travel_date": "2026-11-10",
                "hotel_preference": "budget", "travelers": 2,
            }
        }
    }

    @model_validator(mode="after")
    def _check_date(self):
        if self.travel_date and self.travel_date < date.today():
            raise ValueError("travel_date cannot be in the past")
        return self

    @property
    def all_destination_types(self) -> list[str]:
        types = list(self.destination_types)
        if self.destination_type and self.destination_type not in types:
            types.insert(0, self.destination_type)
        return types


class Recommendation(BaseModel):
    destination_id: int
    destination: str
    state: str
    category: str
    score: float = Field(description="0-100")
    confidence: float = Field(description="0-1; lower when few preferences were given")
    reasons: list[str]
    warnings: list[str]
    components: dict[str, float] = Field(description="Each scoring component on a 0-100 scale")
    estimated_cost: dict[str, int]
    best_seasons: list[int]
    latitude: float
    longitude: float


class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]
    engine: dict
    query: str
    notes: list[str]
