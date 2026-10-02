from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, HttpUrl, StringConstraints


def _check_password(v: str) -> str:
    if len(v.encode()) > 72:  # bcrypt input limit
        raise ValueError("Password is too long")
    if v.isalpha() or v.isdigit():
        raise ValueError("Password must contain letters and at least one number or symbol")
    return v


NewPassword = Annotated[str, Field(min_length=8, max_length=72), AfterValidator(_check_password)]
Email = Annotated[EmailStr, AfterValidator(str.lower)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]


class RegisterRequest(BaseModel):
    name: Name
    email: Email
    password: NewPassword


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    profile_image: str | None
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdate(BaseModel):
    name: Name | None = None
    email: Email | None = None
    profile_image: HttpUrl | None = None


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=72)
    new_password: NewPassword
