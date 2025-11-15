"""Typed wrapper functions for Garth library integration.

This module provides type-safe wrappers around the Garth library to:
1. Enable mypy type checking (eliminating `type: ignore` comments)
2. Detect API changes early through runtime validation
3. Improve code maintainability with explicit type signatures

All wrappers use non-blocking validation: validation failures log warnings
but return raw data, allowing recovery from Garth API changes.
"""

import logging

from pydantic import BaseModel


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
