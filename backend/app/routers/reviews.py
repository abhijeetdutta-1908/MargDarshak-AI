from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.review import ReviewIn, ReviewOut, ReviewPage, ReviewUpdate
from app.security import get_current_user
from app.services import reviews as svc

router = APIRouter(tags=["reviews"])


@router.get("/api/destinations/{destination_id}/reviews", response_model=ReviewPage)
def list_reviews(destination_id: int, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
                 db: Session = Depends(get_db)):
    """Average rating, star distribution and the latest visible reviews."""
    return svc.list_for_destination(db, destination_id, page, page_size)


@router.post("/api/destinations/{destination_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(destination_id: int, data: ReviewIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """One review per user per destination."""
    return svc.create(db, user, destination_id, data)


@router.put("/api/reviews/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, data: ReviewUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.update(db, svc.get_editable(db, user, review_id), data)


@router.delete("/api/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.delete(db, svc.get_editable(db, user, review_id))


@router.get("/api/reviews/me", response_model=list[ReviewOut])
def my_reviews(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.mine(db, user)


@router.get("/api/reviews/recent", response_model=list[ReviewOut])
def recent_reviews(limit: int = Query(6, ge=1, le=20), db: Session = Depends(get_db)):
    """Highly rated recent reviews from real users (used on the landing page)."""
    return svc.recent(db, limit)
