from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Destination, Hotel, Place, Review, SavedTrip, User
from app.schemas.admin import DestinationIn, HotelIn
from app.services.catalog import get_destination
from app.services.recommendations import invalidate_catalog


def stats(db: Session) -> dict:
    count = lambda m: db.scalar(select(func.count()).select_from(m))  # noqa: E731
    return {
        "users": count(User), "destinations": count(Destination), "hotels": count(Hotel), "places": count(Place),
        "trips": count(SavedTrip), "reviews": count(Review),
        "hidden_reviews": db.scalar(select(func.count()).where(Review.is_hidden.is_(True))),
    }


def _check_days(data: DestinationIn) -> None:
    if data.ideal_min_days > data.ideal_max_days:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "ideal_min_days cannot exceed ideal_max_days")
    if any(not 1 <= m <= 12 for m in data.best_seasons):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "best_seasons must be month numbers 1-12")


def create_destination(db: Session, data: DestinationIn) -> Destination:
    _check_days(data)
    if db.scalar(select(Destination).where(func.lower(Destination.name) == data.name.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "A destination with this name already exists")
    dest = Destination(**data.model_dump())
    db.add(dest)
    db.commit()
    db.refresh(dest)
    invalidate_catalog()
    return dest


def update_destination(db: Session, destination_id: int, data: DestinationIn) -> Destination:
    _check_days(data)
    dest = get_destination(db, destination_id)
    for k, v in data.model_dump().items():
        setattr(dest, k, v)
    db.commit()
    db.refresh(dest)
    invalidate_catalog()
    return dest


def delete_destination(db: Session, destination_id: int) -> None:
    dest = get_destination(db, destination_id)
    if db.scalar(select(func.count()).where(SavedTrip.destination_id == dest.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Users have trips to this destination; it can't be deleted")
    db.delete(dest)
    db.commit()
    invalidate_catalog()


def get_hotel(db: Session, hotel_id: int) -> Hotel:
    hotel = db.get(Hotel, hotel_id)
    if hotel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hotel not found")
    return hotel


def save_hotel(db: Session, data: HotelIn, hotel: Hotel | None = None) -> Hotel:
    get_destination(db, data.destination_id)
    hotel = hotel or Hotel()
    for k, v in data.model_dump().items():
        setattr(hotel, k, v)
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    invalidate_catalog()
    return hotel


def delete_hotel(db: Session, hotel_id: int) -> None:
    db.delete(get_hotel(db, hotel_id))  # trips keep working: saved_trips.hotel_id is SET NULL
    db.commit()
    invalidate_catalog()


def list_users(db: Session, q: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
    stmt = select(User)
    if q:
        stmt = stmt.where(or_(User.name.icontains(q, autoescape=True), User.email.icontains(q, autoescape=True)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    users = db.scalars(stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)).all()
    trips = dict(db.execute(select(SavedTrip.user_id, func.count()).group_by(SavedTrip.user_id)).all())
    reviews = dict(db.execute(select(Review.user_id, func.count()).group_by(Review.user_id)).all())
    return [{"id": u.id, "name": u.name, "email": u.email, "is_admin": u.is_admin,
             "trip_count": trips.get(u.id, 0), "review_count": reviews.get(u.id, 0)} for u in users], total


def set_admin(db: Session, actor: User, user_id: int, is_admin: bool) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == actor.id and not is_admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't remove your own admin access")
    user.is_admin = is_admin
    db.commit()
    return user


def list_reviews(db: Session, hidden: bool | None, page: int, page_size: int) -> tuple[list[Review], int]:
    stmt = select(Review)
    if hidden is not None:
        stmt = stmt.where(Review.is_hidden.is_(hidden))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Review.created_at.desc(), Review.id.desc())
                       .offset((page - 1) * page_size).limit(page_size)).all()
    return list(items), total


def get_review(db: Session, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return review


def moderate(db: Session, review_id: int, hidden: bool) -> Review:
    review = get_review(db, review_id)
    review.is_hidden = hidden
    db.commit()
    db.refresh(review)
    return review
