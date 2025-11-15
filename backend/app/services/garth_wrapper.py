"""Typed wrapper functions for Garth library integration.

This module provides type-safe wrappers around the Garth library to:
1. Enable mypy type checking (eliminating `type: ignore` comments)
2. Detect API changes early through runtime validation
3. Improve code maintainability with explicit type signatures

All wrappers use non-blocking validation: validation failures log warnings
but return raw data, allowing recovery from Garth API changes.
"""

import logging
from typing import Any

import garth
from pydantic import BaseModel, ValidationError
from telemetry.logging_utils import redact_for_logging


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
