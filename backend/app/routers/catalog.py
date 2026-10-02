from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.catalog import DestinationDetail, DestinationPage, HotelList
from app.schemas.preferences import DestinationType, HotelTier
from app.services import catalog as svc

router = APIRouter(tags=["destinations"])


@router.get("/api/destinations", response_model=DestinationPage)
def list_destinations(
    category: DestinationType | None = None,
    q: str | None = Query(None, max_length=80, description="Matches name, state, description or tags"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Browse destinations, most popular first."""
    items, total = svc.list_destinations(db, q=q, category=category, page=page, page_size=page_size)
    return DestinationPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/api/destinations/search", response_model=DestinationPage)
def search_destinations(
    q: str = Query(..., min_length=1, max_length=80),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Keyword search, e.g. `kerala`, `trekking`, `beach`."""
    items, total = svc.list_destinations(db, q=q.strip(), category=None, page=page, page_size=page_size)
    return DestinationPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/api/destinations/{destination_id}", response_model=DestinationDetail)
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    return svc.destination_detail(db, destination_id)


@router.get("/api/hotels/{destination_id}", response_model=HotelList, tags=["hotels"])
def list_hotels(
    destination_id: int,
    tier: HotelTier | None = None,
    max_price: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """Hotels at a destination, cheapest first. Seeded sample data (see `note`)."""
    return HotelList(items=svc.list_hotels(db, destination_id, tier=tier, max_price=max_price))
