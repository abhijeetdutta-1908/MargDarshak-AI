from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Destination, Review, User
from app.schemas.review import ReviewIn, ReviewUpdate
from app.services.catalog import get_destination


def to_out(r: Review) -> dict:
    return {
        "id": r.id, "destination_id": r.destination_id, "destination_name": r.destination.name,
        "user_id": r.user_id, "user_name": r.user.name, "rating": r.rating, "comment": r.comment,
        "is_hidden": r.is_hidden, "created_at": r.created_at, "updated_at": r.updated_at,
    }


def rating_summary(db: Session, destination_id: int) -> tuple[float | None, int, dict[int, int]]:
    rows = db.execute(
        select(Review.rating, func.count()).where(Review.destination_id == destination_id, Review.is_hidden.is_(False))
        .group_by(Review.rating)
    ).all()
    dist = {i: 0 for i in range(1, 6)} | {r: n for r, n in rows}
    count = sum(dist.values())
    avg = round(sum(r * n for r, n in dist.items()) / count, 2) if count else None
    return avg, count, dist


def list_for_destination(db: Session, destination_id: int, page: int, page_size: int) -> dict:
    get_destination(db, destination_id)
    stmt = select(Review).where(Review.destination_id == destination_id, Review.is_hidden.is_(False))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Review.updated_at.desc(), Review.id.desc())
                       .offset((page - 1) * page_size).limit(page_size)).all()
    avg, count, dist = rating_summary(db, destination_id)
    return {"average_rating": avg, "review_count": count, "distribution": dist, "items": [to_out(r) for r in items],
            "total": total, "page": page, "page_size": page_size}


def create(db: Session, user: User, destination_id: int, data: ReviewIn) -> dict:
    get_destination(db, destination_id)
    review = Review(user_id=user.id, destination_id=destination_id, rating=data.rating, comment=data.comment)
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already reviewed this destination. Edit your review instead.") from None
    db.refresh(review)
    return to_out(review)


def get_editable(db: Session, user: User, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    if review.user_id != user.id and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only change your own reviews")
    return review


def update(db: Session, review: Review, data: ReviewUpdate) -> dict:
    for k, v in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(review, k, v)
    db.commit()
    db.refresh(review)
    return to_out(review)


def delete(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()


def mine(db: Session, user: User) -> list[dict]:
    return [to_out(r) for r in db.scalars(select(Review).where(Review.user_id == user.id).order_by(Review.updated_at.desc()))]


def recent(db: Session, limit: int) -> list[dict]:
    stmt = (select(Review).join(Destination).where(Review.is_hidden.is_(False), func.length(Review.comment) >= 20)
            .order_by(Review.rating.desc(), Review.updated_at.desc()).limit(limit))
    return [to_out(r) for r in db.scalars(stmt)]
