from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173"

    # Optional external APIs; each service falls back to labelled seeded data without them.
    google_maps_api_key: str | None = None
    google_places_api_key: str | None = None
    openweather_api_key: str | None = None
    # Sent to browsers for the Maps JavaScript API, so it must be a separate key restricted by HTTP referrer.
    google_maps_browser_key: str | None = None
    http_timeout_seconds: float = 6.0
    weather_cache_seconds: int = 1800
    places_cache_seconds: int = 6 * 3600

    # JSON object overriding RecommendationEngine weights, e.g. {"budget": 0.3}
    recommendation_weights: dict[str, float] | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def places_key(self) -> str | None:
        return self.google_places_api_key or self.google_maps_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
