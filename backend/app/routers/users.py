from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.preferences import PreferencesIn, PreferencesOut
from app.schemas.user import PasswordChange, TokenResponse, UserOut, UserUpdate
from app.security import create_access_token, get_current_user
from app.services import users as svc

router = APIRouter(tags=["users"])


@router.get("/api/users/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/api/users/me", response_model=UserOut)
def update_me(data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.update_profile(db, user, data)


@router.post("/api/users/me/password", response_model=TokenResponse)
def change_password(data: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change password. Other sessions are signed out; a fresh token is returned for this one."""
    user = svc.change_password(db, user, data)
    return TokenResponse(access_token=create_access_token(user), user=user)


@router.get("/api/preferences", response_model=PreferencesOut, tags=["preferences"])
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.get_preferences(db, user)


@router.put("/api/preferences", response_model=PreferencesOut, tags=["preferences"])
def put_preferences(data: PreferencesIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.upsert_preferences(db, user, data)
