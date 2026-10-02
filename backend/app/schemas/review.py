from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Comment = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Comment = ""


class ReviewUpdate(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    comment: Comment | None = None


class ReviewOut(BaseModel):
    id: int
    destination_id: int
    destination_name: str
    user_id: int
    user_name: str
    rating: int
    comment: str
    is_hidden: bool
    created_at: datetime
    updated_at: datetime


class ReviewPage(BaseModel):
    average_rating: float | None
    review_count: int
    distribution: dict[int, int]
    items: list[ReviewOut]
    total: int
    page: int
    page_size: int
