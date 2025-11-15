"""Typed wrapper functions for Garth library integration.

This module provides type-safe wrappers around the Garth library to:
1. Enable mypy type checking (eliminating `type: ignore` comments)
2. Detect API changes early through runtime validation
3. Improve code maintainability with explicit type signatures

All wrappers use non-blocking validation: validation failures log warnings
but return raw data, allowing recovery from Garth API changes.
"""

import logging
from datetime import UTC, date, datetime
from typing import Any

import garth
from pydantic import BaseModel, ValidationError
from telemetry.logging_utils import redact_for_logging

from app.models.garmin_data import DailyMetrics, GarminActivity, HealthSnapshot


logger = logging.getLogger(__name__)


class GarthOAuth1Token(BaseModel):
    """Minimal schema for OAuth1 token structure."""

    oauth_token: str
    oauth_token_secret: str
    # Allow additional fields Garth may include
    model_config = {"extra": "allow"}


class GarthOAuth2Token(BaseModel):
    """Minimal schema for OAuth2 token structure."""

    access_token: str
    token_type: str = "Bearer"  # noqa: S105
    expires_in: int | None = None
    refresh_token: str | None = None
    model_config = {"extra": "allow"}


class GarthProfileResponse(BaseModel):
    """Minimal schema for user profile data from Garth."""

    displayName: str | None = None  # noqa: N815
    model_config = {"extra": "allow"}


# OAuth Token Operations


def get_oauth1_token() -> dict[str, Any]:
    """Get OAuth1 token from garth.client with type safety.

    Returns:
        OAuth1 token dictionary with validated structure

    Raises:
        AttributeError: If garth.client.oauth1_token not available

    Note:
        Logs warning if token structure changes but returns raw data
    """
    raw_token = garth.client.oauth1_token

    # Validate structure (non-blocking)
    try:
        GarthOAuth1Token.model_validate(raw_token)
    except ValidationError as e:
        logger.warning(
            "Garth OAuth1 token structure changed: %s",
            redact_for_logging(str(e)),
        )

    return raw_token


def set_oauth1_token(token: dict[str, Any]) -> None:
    """Set OAuth1 token on garth.client with type validation.

    Args:
        token: OAuth1 token dictionary

    Note:
        Logs warning if token structure unexpected but still sets token.
        Non-blocking approach allows recovery from minor schema changes.
    """
    # Validate before setting (non-blocking)
    try:
        GarthOAuth1Token.model_validate(token)
    except ValidationError as e:
        logger.warning(
            "Setting possibly invalid OAuth1 token: %s",
            redact_for_logging(str(e)),
        )

    garth.client.oauth1_token = token


def get_oauth2_token() -> dict[str, Any]:
    """Get OAuth2 token from garth.client with type safety.

    Returns:
        OAuth2 token dictionary with validated structure

    Raises:
        AttributeError: If garth.client.oauth2_token not available

    Note:
        Logs warning if token structure changes but returns raw data
    """
    raw_token = garth.client.oauth2_token

    # Validate structure (non-blocking)
    try:
        GarthOAuth2Token.model_validate(raw_token)
    except ValidationError as e:
        logger.warning(
            "Garth OAuth2 token structure changed: %s",
            redact_for_logging(str(e)),
        )

    return raw_token


def set_oauth2_token(token: dict[str, Any]) -> None:
    """Set OAuth2 token on garth.client with type validation.

    Args:
        token: OAuth2 token dictionary

    Note:
        Logs warning if token structure unexpected but still sets token.
        Non-blocking approach allows recovery from minor schema changes.
    """
    # Validate before setting (non-blocking)
    try:
        GarthOAuth2Token.model_validate(token)
    except ValidationError as e:
        logger.warning(
            "Setting possibly invalid OAuth2 token: %s",
            redact_for_logging(str(e)),
        )

    garth.client.oauth2_token = token


# Data Retrieval Operations


def get_activities_typed(date_str: str) -> list[dict[str, Any]]:
    """Fetch activities for a specific date with runtime type validation.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD)

    Returns:
        List of activity dictionaries with validated structure

    Raises:
        Exception: If Garth API call fails

    Note:
        Logs warning if Garth response structure changes, but returns raw data.
        Uses existing GarminActivity model for validation.
    """
    raw_activities = garth.activities(date_str)

    # Validate structure of each activity using existing model
    try:
        for activity in raw_activities:
            GarminActivity(**activity)
    except ValidationError as e:
        logger.warning(
            "Garth activities response structure changed for %s: %s",
            date_str,
            redact_for_logging(str(e)),
        )

    return raw_activities


def get_daily_summary_typed(date_str: str) -> dict[str, Any]:
    """Fetch daily summary for a specific date with runtime type validation.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD)

    Returns:
        Daily summary dictionary with validated structure

    Raises:
        Exception: If Garth API call fails

    Note:
        Logs warning if Garth response structure changes, but returns raw data.
        Validates against expected DailyMetrics fields (steps, distanceMeters, etc.).
    """
    raw_summary = garth.daily_summary(date_str)

    # Validate structure - DailyMetrics expects specific field names
    try:
        # Create temporary DailyMetrics to validate structure
        DailyMetrics(
            date=date.fromisoformat(date_str),
            steps=raw_summary.get("steps"),
            distance_meters=raw_summary.get("distanceMeters"),
            active_calories=raw_summary.get("activeCalories"),
            resting_heart_rate=raw_summary.get("restingHeartRate"),
            max_heart_rate=raw_summary.get("maxHeartRate"),
            avg_stress_level=raw_summary.get("avgStressLevel"),
            sleep_seconds=raw_summary.get("sleepSeconds"),
        )
    except ValidationError as e:
        logger.warning(
            "Garth daily_summary response structure changed for %s: %s",
            date_str,
            redact_for_logging(str(e)),
        )

    return raw_summary


def get_health_snapshot_typed() -> dict[str, Any]:
    """Fetch latest health snapshot with runtime type validation.

    Returns:
        Health snapshot dictionary with validated structure

    Raises:
        Exception: If Garth API call fails

    Note:
        Logs warning if Garth response structure changes, but returns raw data.
        Validates against HealthSnapshot expected fields.
    """
    raw_snapshot = garth.health_snapshot()

    # Validate structure
    try:
        HealthSnapshot(
            timestamp=datetime.now(UTC),
            heart_rate=raw_snapshot.get("heartRate"),
            respiration_rate=raw_snapshot.get("respirationRate"),
            stress_level=raw_snapshot.get("stressLevel"),
            spo2=raw_snapshot.get("spo2"),
        )
    except ValidationError as e:
        logger.warning(
            "Garth health_snapshot response structure changed: %s",
            redact_for_logging(str(e)),
        )

    return raw_snapshot


def get_user_profile_typed() -> dict[str, Any]:
    """Get user profile from garth.client with type safety.

    Returns:
        User profile dictionary with validated structure

    Raises:
        AttributeError: If garth.client.profile not available

    Note:
        Logs warning if Garth response structure changes, but returns raw data.
        According to garmin_service.py:198, garth.client.profile is a dict.
    """
    raw_profile = garth.client.profile

    # Validate structure
    try:
        GarthProfileResponse.model_validate(raw_profile)
    except ValidationError as e:
        logger.warning(
            "Garth profile structure changed: %s",
            redact_for_logging(str(e)),
        )

    return raw_profile
