from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model for Firestore."""
    uid: str  # Firebase user ID
    email: EmailStr
    created_at: datetime


class UserCreate(BaseModel):
    """Schema for creating a user (used for registration info)."""
    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Schema for reading user data."""
    uid: str
    email: EmailStr
    created_at: datetime
