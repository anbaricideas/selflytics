"""Garmin OAuth token storage model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class GarminToken(BaseModel):
    """Garmin OAuth tokens stored in Firestore."""

    user_id: str
    oauth1_token_encrypted: str  # Encrypted before storage
    oauth2_token_encrypted: str  # Encrypted before storage
    token_expiry: datetime | None = None
    last_sync: datetime | None = None
    mfa_enabled: bool = False
    created_at: datetime
    updated_at: datetime


class GarminTokenDecrypted(BaseModel):
    """Decrypted tokens for use in GarminClient."""

    oauth1_token: dict[str, Any]
    oauth2_token: dict[str, Any]
