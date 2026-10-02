"""Trip generation pipeline and saved-trip management.

generate():  validate -> recommend -> pick destination -> weather -> places -> rank hotels
             -> itinerary (weather-aware, route-optimised) -> budget -> save -> return
"""

import math
import secrets
from collections import Counter
from datetime import date, timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.budget import BudgetCalculator, CostProfile
from app.ml.hotels import HotelCandidate, rank_hotels
from app.ml.itinerary import DayWeather, HotelStay, ItineraryGenerator, PlaceItem
from app.ml.recommendation import haversine_km
from app.models import Destination, Hotel, ItineraryItem, Place, Review, SavedTrip, TravelHistory, TripDay, User
from app.schemas.recommendation import RecommendationRequest
from app.schemas.trip import TripGenerateRequest, TripUpdate
from app.services import recommendations, weather
from app.services.catalog import get_destination

ROOM_SHARE = 0.45  # share of the budget we assume goes on rooms when ranking hotels


# ---- planning ------------------------------------------------------------------------------
def _hotels_ranked(db: Session, dest: Destination, values: dict) -> list[dict]:
    hotels = db.scalars(select(Hotel).where(Hotel.destination_id == dest.id)).all()
    attractions = db.execute(
        select(Place.latitude, Place.longitude).where(Place.destination_id == dest.id, Place.kind == "attraction")
    ).all()
    nights = max(1, values["duration"] - 1)
    rooms = math.ceil(values["travelers"] / 2)
    nightly = values["budget"] * ROOM_SHARE / nights / rooms
    cands = [HotelCandidate(h.id, h.name, h.tier, h.rating, h.price_per_night, h.latitude, h.longitude) for h in hotels]
    ranked = rank_hotels(cands, values.get("hotel_preference"), nightly, [tuple(a) for a in attractions])
    by_id = {h.id: h for h in hotels}
    return [{"hotel": by_id[r["hotel"].id], "score": r["score"], "reasons": r["reasons"]} for r in ranked]


async def _plan(db: Session, http: httpx.AsyncClient, dest: Destination, values: dict, hotel_id: int | None,
                variation: int) -> dict:
    start = date.fromisoformat(values["travel_date"]) if values.get("travel_date") else None
    ranked = _hotels_ranked(db, dest, values)
    if hotel_id is not None:
        chosen = next((r for r in ranked if r["hotel"].id == hotel_id), None)
        if chosen is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "That hotel is not at this destination")
    else:
        chosen = ranked[0] if ranked else None
    hotel = chosen["hotel"] if chosen else None

    wx = await weather.get_weather(http, dest)
    days_weather = []
    for i in range(values["duration"]):
        o = weather.day_outlook(wx, dest, start + timedelta(days=i) if start else None)
        days_weather.append(DayWeather(o["rain_likely"], o["summary"], o["source"]))

    places = [
        PlaceItem(p.id, p.name, p.kind, set(p.tags), p.is_indoor, p.rating or 4.0, p.estimated_cost,
                  p.duration_minutes, p.latitude, p.longitude, p.description, p.address)
        for p in db.scalars(select(Place).where(Place.destination_id == dest.id))
    ]
    itinerary = ItineraryGenerator(
        dest.name, (dest.latitude, dest.longitude), values["duration"], places,
        HotelStay(hotel.id, hotel.name, hotel.latitude, hotel.longitude) if hotel else None,
        values.get("interests") or [], values["travelers"], start, days_weather,
        values.get("food_preference"), values.get("transport_preference"), variation,
    ).generate()

    origin = recommendations.resolve_origin(db, values.get("starting_location"))
    prices: dict[str, list[int]] = {}
    for h in db.scalars(select(Hotel).where(Hotel.destination_id == dest.id)):
        prices.setdefault(h.tier, []).append(h.price_per_night)
    profile = CostProfile(dest.name, dest.average_daily_cost, dest.average_hotel_cost, dest.average_food_cost,
                          dest.average_transport_cost, prices)
    budget = BudgetCalculator(
        profile, values["duration"], values["travelers"], hotel.tier if hotel else values.get("hotel_preference"),
        values.get("transport_preference"), hotel_price=hotel.price_per_night if hotel else None,
        activity_cost_per_person=itinerary["activity_cost_per_person"],
        intercity_km=haversine_km(origin[1], (dest.latitude, dest.longitude)) * 1.25 if origin else None,
        origin=origin[0] if origin else None,
    ).calculate_total()
    budget["requested"] = values["budget"]
    budget["within_budget"] = budget["average"] <= values["budget"]
    if chosen:
        budget["hotel_reasons"] = chosen["reasons"]
        budget["hotel_score"] = chosen["score"]
    return {"hotel": hotel, "weather": wx, "itinerary": itinerary, "budget": budget, "start": start}


def _write_days(trip: SavedTrip, dest_id: int, itinerary: dict) -> None:
    trip.days.clear()
    for d in itinerary["days"]:
        day = TripDay(day_number=d["day_number"], date=date.fromisoformat(d["date"]) if d["date"] else None,
                      title=d["title"], weather_note=d["weather"]["summary"], rain_likely=d["weather"]["rain_likely"],
                      weather_source=d["weather"]["source"], total_distance_km=d["total_distance_km"],
                      total_travel_minutes=d["total_travel_minutes"])
        for pos, it in enumerate(d["items"]):
            day.items.append(ItineraryItem(destination_id=dest_id, position=pos, **it))
        trip.days.append(day)
    trip.route = itinerary["route"]
    trip.explanations = itinerary["explanations"]
    trip.unscheduled = itinerary["unscheduled"]


async def generate(db: Session, http: httpx.AsyncClient, user: User, req: TripGenerateRequest) -> SavedTrip:
    rec_req = RecommendationRequest(**req.model_dump(exclude={"destination_id", "hotel_id", "title", "top_k"}), top_k=5)
    recs = recommendations.recommend(db, rec_req)["recommendations"]
    if req.destination_id is not None:
        dest = get_destination(db, req.destination_id)
    elif recs:
        dest = get_destination(db, recs[0]["destination_id"])
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No destination matched these preferences")

    values = req.model_dump(mode="json", exclude={"destination_id", "hotel_id", "title", "top_k"})
    values["destination_types"] = req.all_destination_types
    plan = await _plan(db, http, dest, values, req.hotel_id, variation=0)
    trip = SavedTrip(
        user_id=user.id, destination_id=dest.id, hotel_id=plan["hotel"].id if plan["hotel"] else None,
        title=req.title or f"{req.duration} days in {dest.name}", start_date=plan["start"],
        duration_days=req.duration, travelers=req.travelers, preferences=values, budget=plan["budget"],
        weather=plan["weather"], recommendations=recs,
    )
    _write_days(trip, dest.id, plan["itinerary"])
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


async def regenerate(db: Session, http: httpx.AsyncClient, trip: SavedTrip) -> SavedTrip:
    """New itinerary for the same trip: refreshed weather, alternative picks (variation + 1), same hotel."""
    trip.variation += 1
    plan = await _plan(db, http, trip.destination, trip.preferences, trip.hotel_id, trip.variation)
    trip.weather, trip.budget = plan["weather"], plan["budget"]
    _write_days(trip, trip.destination_id, plan["itinerary"])
    db.commit()
    db.refresh(trip)
    return trip


# ---- management -----------------------------------------------------------------------------
def get_owned(db: Session, user: User, trip_id: int) -> SavedTrip:
    trip = db.get(SavedTrip, trip_id)
    if trip is None or trip.user_id != user.id:  # same 404 either way: don't reveal other users' trips
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    return trip


def list_trips(db: Session, user: User, saved: bool | None, page: int, page_size: int):
    stmt = select(SavedTrip).where(SavedTrip.user_id == user.id)
    if saved is not None:
        stmt = stmt.where(SavedTrip.is_saved == saved)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(SavedTrip.created_at.desc(), SavedTrip.id.desc())
                       .offset((page - 1) * page_size).limit(page_size)).all()
    return list(items), total


def update(db: Session, trip: SavedTrip, data: TripUpdate) -> SavedTrip:
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None or k == "start_date":
            setattr(trip, k, v)
    if "start_date" in data.model_fields_set:
        for day in trip.days:  # keep day dates in step with the new start date
            day.date = trip.start_date + timedelta(days=day.day_number - 1) if trip.start_date else None
    db.commit()
    db.refresh(trip)
    return trip


def delete(db: Session, trip: SavedTrip) -> None:
    db.delete(trip)
    db.commit()


def duplicate(db: Session, trip: SavedTrip) -> SavedTrip:
    copy = SavedTrip(
        user_id=trip.user_id, destination_id=trip.destination_id, hotel_id=trip.hotel_id,
        title=f"{trip.title} (copy)"[:160], start_date=trip.start_date, duration_days=trip.duration_days,
        travelers=trip.travelers, preferences=trip.preferences, budget=trip.budget, weather=trip.weather,
        route=trip.route, recommendations=trip.recommendations, explanations=trip.explanations,
        unscheduled=trip.unscheduled, variation=trip.variation, is_saved=True,
    )
    for d in trip.days:
        day = TripDay(**{c: getattr(d, c) for c in ("day_number", "date", "title", "weather_note", "rain_likely",
                                                     "weather_source", "total_distance_km", "total_travel_minutes")})
        for it in d.items:
            day.items.append(ItineraryItem(**{c.key: getattr(it, c.key) for c in ItineraryItem.__table__.columns
                                              if c.key not in ("id", "trip_day_id")}))
        copy.days.append(day)
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


def share(db: Session, trip: SavedTrip) -> SavedTrip:
    if not trip.share_token:
        trip.share_token = secrets.token_urlsafe(16)
        db.commit()
    return trip


def unshare(db: Session, trip: SavedTrip) -> None:
    trip.share_token = None
    db.commit()


def get_shared(db: Session, token: str) -> SavedTrip:
    trip = db.scalar(select(SavedTrip).where(SavedTrip.share_token == token)) if token else None
    if trip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This shared trip link is invalid or was revoked")
    return trip


def complete(db: Session, trip: SavedTrip) -> SavedTrip:
    if not trip.is_completed:
        trip.is_completed = True
        db.add(TravelHistory(user_id=trip.user_id, destination_id=trip.destination_id, trip_id=trip.id,
                             visited_on=trip.start_date or date.today()))
        db.commit()
        db.refresh(trip)
    return trip


def dashboard(db: Session, user: User) -> dict:
    trips = db.scalars(select(SavedTrip).where(SavedTrip.user_id == user.id)
                       .order_by(SavedTrip.created_at.desc(), SavedTrip.id.desc())).all()
    today = date.today()
    upcoming = sorted([t for t in trips if t.start_date and t.start_date >= today and not t.is_completed],
                      key=lambda t: t.start_date)
    saved = [t for t in trips if t.is_saved]
    budgets = [t.budget.get("average") for t in saved or trips if t.budget.get("average")]
    counts = Counter(t.destination_id for t in trips)
    for dest_id, in db.execute(select(Review.destination_id).where(Review.user_id == user.id, Review.rating >= 4)):
        counts[dest_id] += 1
    favourites = []
    for dest_id, n in counts.most_common(4):
        d = db.get(Destination, dest_id)
        favourites.append({"id": d.id, "name": d.name, "state": d.state, "category": d.category, "count": n})
    history = db.execute(
        select(TravelHistory, Destination.name).join(Destination, Destination.id == TravelHistory.destination_id)
        .where(TravelHistory.user_id == user.id).order_by(TravelHistory.visited_on.desc())
    ).all()
    return {
        "stats": {"total_trips": len(trips), "saved_trips": len(saved), "completed_trips": sum(t.is_completed for t in trips),
                  "upcoming_trips": len(upcoming),
                  "average_budget": round(sum(budgets) / len(budgets)) if budgets else None},
        "upcoming": upcoming[:3],
        "recent": list(trips[:5]),
        "favourite_destinations": favourites,
        "recent_recommendations": (trips[0].recommendations[:3] if trips else []),
        "travel_history": [{"destination_id": h.destination_id, "destination": name, "trip_id": h.trip_id,
                            "visited_on": h.visited_on} for h, name in history],
    }
