"""Travel catalogue: destinations and the hotels, places and reviews attached to them."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, JSONType

if TYPE_CHECKING:
    from app.models.trip import SavedTrip
    from app.models.user import User


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    state: Mapped[str] = mapped_column(String(80))
    country: Mapped[str] = mapped_column(String(80), default="India")
    description: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(30), index=True)
    tags: Mapped[list] = mapped_column(JSONType, default=list)
    best_seasons: Mapped[list] = mapped_column(JSONType, default=list)  # month numbers 1-12
    ideal_min_days: Mapped[int] = mapped_column(default=2)
    ideal_max_days: Mapped[int] = mapped_column(default=5)
    # Estimated per-person INR costs (seeded estimates, not live prices).
    average_daily_cost: Mapped[int]
    average_hotel_cost: Mapped[int]
    average_food_cost: Mapped[int]
    average_transport_cost: Mapped[int]
    popularity_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0..1
    image_url: Mapped[str | None] = mapped_column(String(500))

    hotels: Mapped[list["Hotel"]] = relationship(back_populates="destination", cascade="all, delete-orphan")
    places: Mapped[list["Place"]] = relationship(back_populates="destination", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="destination", cascade="all, delete-orphan")
    saved_trips: Mapped[list["SavedTrip"]] = relationship(back_populates="destination")


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    tier: Mapped[str] = mapped_column(String(20), index=True)  # budget | standard | premium | luxury
    rating: Mapped[float] = mapped_column(Float)
    price_per_night: Mapped[int]
    address: Mapped[str] = mapped_column(String(255))
    amenities: Mapped[list] = mapped_column(JSONType, default=list)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    image_url: Mapped[str | None] = mapped_column(String(500))

    destination: Mapped[Destination] = relationship(back_populates="hotels")


class Place(Base):
    """Attractions, restaurants, shopping and activities — the fallback for Google Places."""

    __tablename__ = "places"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(20), index=True)  # attraction | restaurant | shopping | activity
    tags: Mapped[list] = mapped_column(JSONType, default=list)
    description: Mapped[str | None] = mapped_column(Text)
    is_indoor: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[float | None] = mapped_column(Float)
    address: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    estimated_cost: Mapped[int] = mapped_column(default=0)  # INR per person
    duration_minutes: Mapped[int] = mapped_column(default=90)
    image_url: Mapped[str | None] = mapped_column(String(500))

    destination: Mapped[Destination] = relationship(back_populates="places")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "destination_id", name="uq_review_user_destination"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int]
    comment: Mapped[str] = mapped_column(Text, default="")
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")  # admin moderation
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="reviews")
    destination: Mapped[Destination] = relationship(back_populates="reviews")
