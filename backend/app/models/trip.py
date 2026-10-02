from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, JSONType

if TYPE_CHECKING:
    from app.models.catalog import Destination, Hotel
    from app.models.user import User


class SavedTrip(Base):
    __tablename__ = "saved_trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="RESTRICT"), index=True)
    hotel_id: Mapped[int | None] = mapped_column(ForeignKey("hotels.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160))
    start_date: Mapped[date | None] = mapped_column(Date)
    duration_days: Mapped[int]
    travelers: Mapped[int] = mapped_column(default=1)
    # Snapshots of what the generator used/produced, so a saved plan stays reproducible.
    preferences: Mapped[dict] = mapped_column(JSONType, default=dict)
    budget: Mapped[dict] = mapped_column(JSONType, default=dict)
    weather: Mapped[dict] = mapped_column(JSONType, default=dict)
    route: Mapped[dict] = mapped_column(JSONType, default=dict)
    recommendations: Mapped[list] = mapped_column(JSONType, default=list)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="saved_trips")
    destination: Mapped["Destination"] = relationship(back_populates="saved_trips")
    hotel: Mapped["Hotel | None"] = relationship()
    days: Mapped[list["TripDay"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", order_by="TripDay.day_number"
    )


class TripDay(Base):
    __tablename__ = "trip_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("saved_trips.id", ondelete="CASCADE"), index=True)
    day_number: Mapped[int]
    date: Mapped[date | None] = mapped_column(Date)
    weather_note: Mapped[str | None] = mapped_column(String(255))

    trip: Mapped[SavedTrip] = relationship(back_populates="days")
    items: Mapped[list["ItineraryItem"]] = relationship(
        back_populates="day", cascade="all, delete-orphan", order_by="ItineraryItem.position"
    )


class ItineraryItem(Base):
    __tablename__ = "itinerary_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_day_id: Mapped[int] = mapped_column(ForeignKey("trip_days.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"))
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id", ondelete="SET NULL"))
    position: Mapped[int]
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[str] = mapped_column(String(5))  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(5))
    location: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(30))
    estimated_cost: Mapped[int] = mapped_column(default=0)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    duration_minutes: Mapped[int] = mapped_column(default=60)

    day: Mapped[TripDay] = relationship(back_populates="items")


class Booking(Base):
    """Placeholder for future booking integration; no payment flow in the MVP."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id", ondelete="CASCADE"))
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("saved_trips.id", ondelete="SET NULL"))
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    guests: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(20), default="planned")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="bookings")


class TravelHistory(Base):
    __tablename__ = "travel_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"))
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("saved_trips.id", ondelete="SET NULL"))
    visited_on: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="travel_history")
