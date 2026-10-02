import httpx
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.trip import ShareResponse, TripDayOut, TripGenerateRequest, TripOut, TripPage, TripSummary, TripUpdate
from app.security import get_current_user
from app.services import trips as svc
from app.services.http import get_http

router = APIRouter(tags=["trips"])


@router.post("/api/trips/generate", response_model=TripOut, status_code=status.HTTP_201_CREATED)
async def generate_trip(req: TripGenerateRequest, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db), http: httpx.AsyncClient = Depends(get_http)):
    """Full pipeline: recommend, pick destination, weather, places, hotel, route, itinerary, budget, save."""
    return await svc.generate(db, http, user, req)


@router.get("/api/trips", response_model=TripPage)
def list_trips(saved: bool | None = None, page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50),
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = svc.list_trips(db, user, saved, page, page_size)
    return TripPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/api/trips/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.get_owned(db, user, trip_id)


@router.put("/api/trips/{trip_id}", response_model=TripOut)
def update_trip(trip_id: int, data: TripUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rename, save/unsave, or change the start date."""
    return svc.update(db, svc.get_owned(db, user, trip_id), data)


@router.delete("/api/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.delete(db, svc.get_owned(db, user, trip_id))


@router.post("/api/trips/{trip_id}/duplicate", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def duplicate_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.duplicate(db, svc.get_owned(db, user, trip_id))


@router.post("/api/trips/{trip_id}/share", response_model=ShareResponse)
def share_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create (or return) a read-only public link token."""
    trip = svc.share(db, svc.get_owned(db, user, trip_id))
    return ShareResponse(share_token=trip.share_token, path=f"/shared/{trip.share_token}")


@router.delete("/api/trips/{trip_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def unshare_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.unshare(db, svc.get_owned(db, user, trip_id))


@router.post("/api/trips/{trip_id}/complete", response_model=TripOut)
def complete_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark as travelled; adds the destination to travel history."""
    return svc.complete(db, svc.get_owned(db, user, trip_id))


@router.get("/api/trips/{trip_id}/itinerary", response_model=list[TripDayOut])
def get_itinerary(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.get_owned(db, user, trip_id).days


@router.post("/api/trips/{trip_id}/itinerary/regenerate", response_model=TripOut)
async def regenerate_itinerary(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                               http: httpx.AsyncClient = Depends(get_http)):
    """Rebuild the day plan with fresh weather and alternative picks; keeps destination and hotel."""
    return await svc.regenerate(db, http, svc.get_owned(db, user, trip_id))


@router.get("/api/shared/{token}", response_model=TripOut, tags=["sharing"])
def shared_trip(token: str, db: Session = Depends(get_db)):
    """Public read-only view of a shared trip (no login)."""
    return svc.get_shared(db, token)


@router.get("/api/dashboard", tags=["dashboard"])
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = svc.dashboard(db, user)
    data["upcoming"] = [TripSummary.model_validate(t) for t in data["upcoming"]]
    data["recent"] = [TripSummary.model_validate(t) for t in data["recent"]]
    return data
