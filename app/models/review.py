from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: str
    user_id: str
    rating: int = Field(ge=1, le=5)
    body: str
    # NEW: sentiment fields
    sentiment_label: Optional[str] = None  # "positive", "negative", "neutral"
    sentiment_score: Optional[float] = None  # confidence / score

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )

class ReviewCreate(SQLModel):
    movie_id: str
    rating: int = Field(ge=1, le=5)
    body: str

class ReviewRead(SQLModel):
    id: int
    movie_id: str
    user_id: str
    rating: int
    body: str
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    created_at: datetime
    updated_at: datetime

class ReviewUpdate(SQLModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    body: Optional[str] = None
