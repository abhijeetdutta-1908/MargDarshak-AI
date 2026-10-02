from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, UserPreference
from app.schemas.preferences import PreferencesIn
from app.schemas.user import PasswordChange, RegisterRequest, UserUpdate
from app.security import hash_password, verify_password

_EMAIL_TAKEN = HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

# Compared against when the email is unknown, so login timing doesn't reveal which emails exist.
_DUMMY_HASH = hash_password("timing-equaliser-1")


def _commit_unique_email(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _EMAIL_TAKEN from None


def register(db: Session, data: RegisterRequest) -> User:
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    _commit_unique_email(db)
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not verify_password(password, user.password_hash if user else _DUMMY_HASH) or user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return user


def revoke_tokens(db: Session, user: User) -> None:
    user.token_version += 1
    db.commit()


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    changes = data.model_dump(exclude_unset=True, mode="json")
    for field, value in changes.items():
        if value is None and field != "profile_image":
            continue  # name/email can't be cleared
        setattr(user, field, value)
    _commit_unique_email(db)
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: PasswordChange) -> User:
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    user.token_version += 1  # sign out other sessions
    db.commit()
    db.refresh(user)
    return user


def get_preferences(db: Session, user: User) -> UserPreference:
    return user.preferences or UserPreference(user_id=user.id, destination_types=[], interests=[])


def upsert_preferences(db: Session, user: User, data: PreferencesIn) -> UserPreference:
    prefs = user.preferences or UserPreference(user_id=user.id)
    for field, value in data.model_dump().items():
        setattr(prefs, field, value)
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs
