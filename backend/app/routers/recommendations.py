from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services import recommendations as svc
from app.utils.ratelimit import recommend_limit

router = APIRouter(tags=["recommendations"])


@router.post("/api/recommendations", response_model=RecommendationResponse, dependencies=[Depends(recommend_limit)])
def recommend(req: RecommendationRequest, db: Session = Depends(get_db)):
    """Rank destinations for the given preferences.

    Each result has a 0-100 score, a confidence, the per-component scores, plain-language
    reasons and warnings, and an estimated cost range.
    """
    return svc.recommend(db, req)
