"""Unit tests for Garth wrapper functions."""

import pytest
from pydantic import ValidationError

from app.services.garth_wrapper import (
    GarthOAuth1Token,
    GarthOAuth2Token,
    GarthProfileResponse,
)


class TestTokenModels:
    """Test token validation models."""

    def test_oauth1_token_valid_structure(self):
        """Valid OAuth1 token should be accepted."""
        token_data = {
            "oauth_token": "token_123",
            "oauth_token_secret": "secret_456",
        }

        token = GarthOAuth1Token(**token_data)

        assert token.oauth_token == "token_123"  # noqa: S105
        assert token.oauth_token_secret == "secret_456"  # noqa: S105

    def test_oauth1_token_extra_fields_allowed(self):
        """OAuth1 token with extra fields should not cause errors."""
        token_data = {
            "oauth_token": "token_123",
            "oauth_token_secret": "secret_456",
            "extra_field": "extra_value",
            "another_field": 123,
        }

        # Should not raise ValidationError
        token = GarthOAuth1Token(**token_data)

        assert token.oauth_token == "token_123"  # noqa: S105
        assert token.oauth_token_secret == "secret_456"  # noqa: S105

    def test_oauth1_token_missing_required_fails(self):
        """OAuth1 token missing required fields should be detected."""
        token_data = {
            "oauth_token": "token_123",
            # Missing oauth_token_secret
        }

        with pytest.raises(ValidationError):
            GarthOAuth1Token(**token_data)

    def test_oauth2_token_valid_structure(self):
        """Valid OAuth2 token should be accepted."""
        token_data = {
            "access_token": "access_123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh_456",
        }

        token = GarthOAuth2Token(**token_data)

        assert token.access_token == "access_123"  # noqa: S105
        assert token.token_type == "Bearer"  # noqa: S105
        assert token.expires_in == 3600
        assert token.refresh_token == "refresh_456"  # noqa: S105

    def test_oauth2_token_minimal_fields(self):
        """OAuth2 token with only required field should be accepted."""
        token_data = {
            "access_token": "access_123",
        }

        token = GarthOAuth2Token(**token_data)

        assert token.access_token == "access_123"  # noqa: S105
        assert token.token_type == "Bearer"  # noqa: S105
        assert token.expires_in is None
        assert token.refresh_token is None

    def test_oauth2_token_extra_fields_allowed(self):
        """OAuth2 token with extra fields should not cause errors."""
        token_data = {
            "access_token": "access_123",
            "extra_field": "extra_value",
        }

        # Should not raise ValidationError
        token = GarthOAuth2Token(**token_data)

        assert token.access_token == "access_123"  # noqa: S105

    def test_profile_response_valid(self):
        """Valid profile response should be accepted."""
        profile_data = {
            "displayName": "John Doe",
            "extra_field": "extra_value",
        }

        profile = GarthProfileResponse(**profile_data)

        assert profile.displayName == "John Doe"

    def test_profile_response_empty(self):
        """Profile response with no displayName should be accepted."""
        profile_data = {}

        profile = GarthProfileResponse(**profile_data)

        assert profile.displayName is None
