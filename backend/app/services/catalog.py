from fastapi import HTTPException, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models import Destination, Hotel, Place


def get_destination(db: Session, destination_id: int) -> Destination:
    dest = db.get(Destination, destination_id)
    if dest is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Destination not found")
    return dest


def list_destinations(
    db: Session, *, q: str | None, category: str | None, page: int, page_size: int
) -> tuple[list[Destination], int]:
    stmt = select(Destination)
    if category:
        stmt = stmt.where(Destination.category == category)
    if q:
        stmt = stmt.where(
            or_(
                Destination.name.icontains(q, autoescape=True),
                Destination.state.icontains(q, autoescape=True),
                Destination.description.icontains(q, autoescape=True),
                cast(Destination.tags, String).icontains(q, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(Destination.popularity_score.desc(), Destination.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def destination_detail(db: Session, destination_id: int) -> dict:
    dest = get_destination(db, destination_id)
    kinds = dict(
        db.execute(
            select(Place.kind, func.count()).where(Place.destination_id == dest.id).group_by(Place.kind)
        ).all()
    )
    hotels = db.scalar(select(func.count()).where(Hotel.destination_id == dest.id))
    return {
        **{c.key: getattr(dest, c.key) for c in Destination.__table__.columns},
        "attraction_count": kinds.get("attraction", 0),
        "restaurant_count": kinds.get("restaurant", 0),
        "hotel_count": hotels,
    }


def list_hotels(
    db: Session, destination_id: int, *, tier: str | None, max_price: int | None
) -> list[Hotel]:
    get_destination(db, destination_id)
    stmt = select(Hotel).where(Hotel.destination_id == destination_id)
    if tier:
        stmt = stmt.where(Hotel.tier == tier)
    if max_price is not None:
        stmt = stmt.where(Hotel.price_per_night <= max_price)
    return list(db.scalars(stmt.order_by(Hotel.price_per_night)))
