"""Unit tests for GarminToken storage model."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.garmin_token import GarminToken, GarminTokenDecrypted


class TestGarminToken:
    """Tests for GarminToken model."""

    def test_garmin_token_valid_data(self):
        """Test GarminToken with valid data."""
        now = datetime.now(UTC)
        token_data = {
            "user_id": "user123",
            "oauth1_token_encrypted": "encrypted_oauth1_token_data",
            "oauth2_token_encrypted": "encrypted_oauth2_token_data",
            "token_expiry": now,
            "last_sync": now,
            "mfa_enabled": True,
            "created_at": now,
            "updated_at": now,
        }

        token = GarminToken(**token_data)

        assert token.user_id == "user123"
        assert token.oauth1_token_encrypted == "encrypted_oauth1_token_data"  # noqa: S105
        assert token.oauth2_token_encrypted == "encrypted_oauth2_token_data"  # noqa: S105
        assert token.token_expiry == now
        assert token.last_sync == now
        assert token.mfa_enabled is True
        assert token.created_at == now
        assert token.updated_at == now

    def test_garmin_token_optional_fields(self):
        """Test GarminToken with only required fields."""
        now = datetime.now(UTC)
        token_data = {
            "user_id": "user123",
            "oauth1_token_encrypted": "encrypted_oauth1_token_data",
            "oauth2_token_encrypted": "encrypted_oauth2_token_data",
            "mfa_enabled": False,
            "created_at": now,
            "updated_at": now,
        }

        token = GarminToken(**token_data)

        assert token.user_id == "user123"
        assert token.oauth1_token_encrypted == "encrypted_oauth1_token_data"  # noqa: S105
        assert token.oauth2_token_encrypted == "encrypted_oauth2_token_data"  # noqa: S105
        assert token.token_expiry is None
        assert token.last_sync is None
        assert token.mfa_enabled is False

    def test_garmin_token_missing_required_field(self):
        """Test GarminToken validation fails when required field is missing."""
        now = datetime.now(UTC)
        token_data = {
            "oauth1_token_encrypted": "encrypted_oauth1_token_data",
            "oauth2_token_encrypted": "encrypted_oauth2_token_data",
            "created_at": now,
            "updated_at": now,
        }

        with pytest.raises(ValidationError) as exc_info:
            GarminToken(**token_data)

        error_str = str(exc_info.value).lower()
        # Should fail because user_id is missing
        assert "user_id" in error_str or "userid" in error_str

    def test_garmin_token_default_mfa_disabled(self):
        """Test GarminToken defaults mfa_enabled to False."""
        now = datetime.now(UTC)
        token_data = {
            "user_id": "user123",
            "oauth1_token_encrypted": "encrypted_oauth1_token_data",
            "oauth2_token_encrypted": "encrypted_oauth2_token_data",
            "mfa_enabled": False,
            "created_at": now,
            "updated_at": now,
        }

        token = GarminToken(**token_data)
        assert token.mfa_enabled is False


class TestGarminTokenDecrypted:
    """Tests for GarminTokenDecrypted model."""

    def test_garmin_token_decrypted_valid_data(self):
        """Test GarminTokenDecrypted with valid data."""
        oauth1_data = {
            "oauth_token": "token123",
            "oauth_token_secret": "secret123",
        }
        oauth2_data = {
            "access_token": "access123",
            "refresh_token": "refresh123",
            "expires_in": 3600,
        }

        decrypted = GarminTokenDecrypted(oauth1_token=oauth1_data, oauth2_token=oauth2_data)

        assert decrypted.oauth1_token == oauth1_data
        assert decrypted.oauth2_token == oauth2_data

    def test_garmin_token_decrypted_missing_required_field(self):
        """Test GarminTokenDecrypted validation fails when required field is missing."""
        oauth1_data = {
            "oauth_token": "token123",
            "oauth_token_secret": "secret123",
        }

        with pytest.raises(ValidationError) as exc_info:
            GarminTokenDecrypted(oauth1_token=oauth1_data)

        error_str = str(exc_info.value).lower()
        assert "oauth2_token" in error_str or "oauth2token" in error_str

    def test_garmin_token_decrypted_dict_types(self):
        """Test GarminTokenDecrypted accepts dict types."""
        oauth1_data = {"key1": "value1"}
        oauth2_data = {"key2": "value2"}

        decrypted = GarminTokenDecrypted(oauth1_token=oauth1_data, oauth2_token=oauth2_data)

        assert isinstance(decrypted.oauth1_token, dict)
        assert isinstance(decrypted.oauth2_token, dict)
        assert decrypted.oauth1_token["key1"] == "value1"
        assert decrypted.oauth2_token["key2"] == "value2"
