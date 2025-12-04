from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Review(BaseModel):
    """Review model for Firestore."""
    id: Optional[str] = None  # Firestore document ID
    movie_id: str
    user_id: str  # Firebase user ID
    rating: int = Field(ge=1, le=5)
    body: str
    # Sentiment fields
    sentiment_label: Optional[str] = None  # "positive", "negative", "neutral"
    sentiment_score: Optional[float] = None  # confidence / score
    created_at: datetime
    updated_at: datetime


class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    movie_id: str
    rating: int = Field(ge=1, le=5)
    body: str


class ReviewRead(BaseModel):
    """Schema for reading review data."""
    id: str
    movie_id: str
    user_id: str
    rating: int
    body: str
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    created_at: datetime
    updated_at: datetime


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    body: Optional[str] = None
