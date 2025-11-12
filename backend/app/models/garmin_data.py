"""Garmin data models based on API responses."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class GarminActivity(BaseModel):
    """Activity from Garmin Connect."""

    model_config = ConfigDict(populate_by_name=True)

    activity_id: int = Field(..., alias="activityId")
    activity_name: str = Field(..., alias="activityName")
    activity_type: str = Field(..., alias="activityType")
    start_time_local: datetime = Field(..., alias="startTimeLocal")
    distance_meters: float | None = Field(None, alias="distance")
    duration_seconds: int | None = Field(None, alias="duration")
    average_hr: int | None = Field(None, alias="averageHR")
    calories: int | None = Field(None, alias="calories")
    elevation_gain: float | None = Field(None, alias="elevationGain")


class DailyMetrics(BaseModel):
    """Daily summary metrics from Garmin."""

    date: date
    steps: int | None = None
    distance_meters: float | None = None
    active_calories: int | None = None
    resting_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_stress_level: int | None = None
    sleep_seconds: int | None = None


class HealthSnapshot(BaseModel):
    """Real-time health snapshot."""

    timestamp: datetime
    heart_rate: int | None = None
    respiration_rate: int | None = None
    stress_level: int | None = None
    spo2: float | None = None


class GarminUserProfile(BaseModel):
    """User profile from Garmin Connect."""

    user_id: str
    display_name: str
    email: str | None = None
    profile_image_url: str | None = None
