from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.admin import AdminUserUpdate, DestinationIn, HotelIn, ModerationUpdate
from app.schemas.catalog import DestinationOut, HotelOut
from app.security import require_admin
from app.services import admin as svc
from app.services import catalog
from app.services.reviews import delete as delete_review_svc
from app.services.reviews import to_out

# Every route here requires an admin token.
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return svc.stats(db)


@router.post("/destinations", response_model=DestinationOut, status_code=status.HTTP_201_CREATED)
def create_destination(data: DestinationIn, db: Session = Depends(get_db)):
    return svc.create_destination(db, data)


@router.put("/destinations/{destination_id}", response_model=DestinationOut)
def update_destination(destination_id: int, data: DestinationIn, db: Session = Depends(get_db)):
    return svc.update_destination(db, destination_id, data)


@router.delete("/destinations/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_destination(destination_id: int, db: Session = Depends(get_db)):
    svc.delete_destination(db, destination_id)


@router.get("/hotels", response_model=list[HotelOut])
def list_hotels(destination_id: int, db: Session = Depends(get_db)):
    return catalog.list_hotels(db, destination_id, tier=None, max_price=None)


@router.post("/hotels", response_model=HotelOut, status_code=status.HTTP_201_CREATED)
def create_hotel(data: HotelIn, db: Session = Depends(get_db)):
    return svc.save_hotel(db, data)


@router.put("/hotels/{hotel_id}", response_model=HotelOut)
def update_hotel(hotel_id: int, data: HotelIn, db: Session = Depends(get_db)):
    return svc.save_hotel(db, data, svc.get_hotel(db, hotel_id))


@router.delete("/hotels/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    svc.delete_hotel(db, hotel_id)


@router.get("/users")
def list_users(q: str | None = Query(None, max_length=80), page: int = Query(1, ge=1),
               page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    items, total = svc.list_users(db, q, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/users/{user_id}")
def update_user(user_id: int, data: AdminUserUpdate, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = svc.set_admin(db, actor, user_id, data.is_admin)
    return {"id": u.id, "is_admin": u.is_admin}


@router.get("/reviews")
def list_reviews(hidden: bool | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 db: Session = Depends(get_db)):
    items, total = svc.list_reviews(db, hidden, page, page_size)
    return {"items": [to_out(r) for r in items], "total": total, "page": page, "page_size": page_size}


@router.put("/reviews/{review_id}")
def moderate_review(review_id: int, data: ModerationUpdate, db: Session = Depends(get_db)):
    """Hide or restore a review. Hidden reviews disappear from public listings and averages."""
    return to_out(svc.moderate(db, review_id, data.is_hidden))


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    delete_review_svc(db, svc.get_review(db, review_id))
