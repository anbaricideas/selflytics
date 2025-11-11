"""User data models for Selflytics."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserProfile(BaseModel):
    """User profile information."""

    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str
    timezone: str = "Australia/Sydney"
    units: Literal["metric", "imperial"] = "metric"


class User(BaseModel):
    """Complete user record stored in Firestore."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str
    email: EmailStr
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    profile: UserProfile
    garmin_linked: bool = False
    garmin_link_date: datetime | None = None


class UserCreate(BaseModel):
    """User registration request data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    display_name: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower()


class UserResponse(BaseModel):
    """User data for API responses (excludes sensitive fields)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str
    email: str
    profile: UserProfile
    garmin_linked: bool
