"""Unit tests for Garth wrapper functions."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.services.garth_wrapper import (
    GarthOAuth1Token,
    GarthOAuth2Token,
    GarthProfileResponse,
    get_activities_typed,
    get_daily_summary_typed,
    get_health_snapshot_typed,
    get_oauth1_token,
    get_oauth2_token,
    get_user_profile_typed,
    set_oauth1_token,
    set_oauth2_token,
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


class TestTokenOperations:
    """Test OAuth token get/set wrapper functions."""

    @patch("app.services.garth_wrapper.garth")
    def test_get_oauth1_token_valid(self, mock_garth):
        """get_oauth1_token should return token when structure is valid."""
        valid_token = {
            "oauth_token": "token_123",
            "oauth_token_secret": "secret_456",
        }
        mock_garth.client.oauth1_token = valid_token

        result = get_oauth1_token()

        assert result == valid_token

    @patch("app.services.garth_wrapper.garth")
    def test_get_oauth1_token_extra_fields(self, mock_garth):
        """get_oauth1_token should accept extra fields without warning."""
        valid_token = {
            "oauth_token": "token_123",
            "oauth_token_secret": "secret_456",
            "extra_field": "extra_value",
        }
        mock_garth.client.oauth1_token = valid_token

        result = get_oauth1_token()

        assert result == valid_token

    @patch("app.services.garth_wrapper.garth")
    @patch("app.services.garth_wrapper.logger")
    def test_get_oauth1_token_missing_required(self, mock_logger, mock_garth):
        """get_oauth1_token should log warning but return data when token invalid."""
        invalid_token = {
            "oauth_token": "token_123",
            # Missing oauth_token_secret
        }
        mock_garth.client.oauth1_token = invalid_token

        result = get_oauth1_token()

        # Should return raw data despite validation error
        assert result == invalid_token
        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "OAuth1 token structure changed" in mock_logger.warning.call_args[0][0]

    @patch("app.services.garth_wrapper.garth")
    def test_set_oauth1_token_valid(self, mock_garth):
        """set_oauth1_token should set token when structure is valid."""
        valid_token = {
            "oauth_token": "token_123",
            "oauth_token_secret": "secret_456",
        }

        set_oauth1_token(valid_token)

        assert mock_garth.client.oauth1_token == valid_token

    @patch("app.services.garth_wrapper.garth")
    @patch("app.services.garth_wrapper.logger")
    def test_set_oauth1_token_invalid(self, mock_logger, mock_garth):
        """set_oauth1_token should log warning but still set invalid token."""
        invalid_token = {
            "oauth_token": "token_123",
            # Missing oauth_token_secret
        }

        set_oauth1_token(invalid_token)

        # Should set token despite validation error
        assert mock_garth.client.oauth1_token == invalid_token
        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "possibly invalid OAuth1 token" in mock_logger.warning.call_args[0][0]

    @patch("app.services.garth_wrapper.garth")
    def test_get_oauth2_token_valid(self, mock_garth):
        """get_oauth2_token should return token when structure is valid."""
        valid_token = {
            "access_token": "access_123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh_456",
        }
        mock_garth.client.oauth2_token = valid_token

        result = get_oauth2_token()

        assert result == valid_token

    @patch("app.services.garth_wrapper.garth")
    @patch("app.services.garth_wrapper.logger")
    def test_get_oauth2_token_missing_required(self, mock_logger, mock_garth):
        """get_oauth2_token should log warning but return data when token invalid."""
        invalid_token = {
            # Missing access_token
            "token_type": "Bearer",
        }
        mock_garth.client.oauth2_token = invalid_token

        result = get_oauth2_token()

        # Should return raw data despite validation error
        assert result == invalid_token
        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "OAuth2 token structure changed" in mock_logger.warning.call_args[0][0]

    @patch("app.services.garth_wrapper.garth")
    def test_set_oauth2_token_valid(self, mock_garth):
        """set_oauth2_token should set token when structure is valid."""
        valid_token = {
            "access_token": "access_123",
            "token_type": "Bearer",
        }

        set_oauth2_token(valid_token)

        assert mock_garth.client.oauth2_token == valid_token

    @patch("app.services.garth_wrapper.garth")
    @patch("app.services.garth_wrapper.logger")
    def test_set_oauth2_token_invalid(self, mock_logger, mock_garth):
        """set_oauth2_token should log warning but still set invalid token."""
        invalid_token = {
            # Missing access_token
            "token_type": "Bearer",
        }

        set_oauth2_token(invalid_token)

        # Should set token despite validation error
        assert mock_garth.client.oauth2_token == invalid_token
        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "possibly invalid OAuth2 token" in mock_logger.warning.call_args[0][0]


class TestDataRetrieval:
    """Test data retrieval wrapper functions."""

    @patch("app.services.garth_wrapper.garth")
    def test_get_activities_typed_valid(self, mock_garth):
        """get_activities_typed should return activities when valid."""
        valid_activities = [
            {
                "activityId": 123,
                "activityName": "Morning Run",
                "activityType": {"typeKey": "running"},
                "startTimeLocal": "2025-11-16T06:00:00",
            }
        ]
        mock_garth.activities.return_value = valid_activities

        result = get_activities_typed("2025-11-16")

        assert result == valid_activities
        mock_garth.activities.assert_called_once_with("2025-11-16")

    @patch("app.services.garth_wrapper.garth")
    def test_get_activities_typed_multiple(self, mock_garth):
        """get_activities_typed should handle multiple activities."""
        valid_activities = [
            {
                "activityId": 123,
                "activityName": "Morning Run",
                "activityType": {"typeKey": "running"},
                "startTimeLocal": "2025-11-16T06:00:00",
            },
            {
                "activityId": 456,
                "activityName": "Afternoon Bike",
                "activityType": {"typeKey": "cycling"},
                "startTimeLocal": "2025-11-16T14:00:00",
            },
        ]
        mock_garth.activities.return_value = valid_activities

        result = get_activities_typed("2025-11-16")

        assert result == valid_activities
        assert len(result) == 2

    @patch("app.services.garth_wrapper.garth")
    @patch("app.services.garth_wrapper.logger")
    def test_get_activities_typed_missing_required(self, mock_logger, mock_garth):
        """get_activities_typed should warn but return data when activity invalid."""
        invalid_activities = [
            {
                "activityId": 123,
                # Missing required fields like activityName, activityType, startTimeLocal
            }
        ]
        mock_garth.activities.return_value = invalid_activities

        result = get_activities_typed("2025-11-16")

        # Should return raw data despite validation error
        assert result == invalid_activities
        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "activities response structure changed" in mock_logger.warning.call_args[0][0]

    @patch("app.services.garth_wrapper.garth")
    @patch("app.services.garth_wrapper.logger")
    def test_get_activities_typed_invalid_type(self, mock_logger, mock_garth):
        """get_activities_typed should warn on type mismatch."""
        invalid_activities = [
            {
                "activityId": "should_be_int_not_string",  # Wrong type
                "activityName": "Test",
                "activityType": {"typeKey": "running"},
                "startTimeLocal": "2025-11-16T06:00:00",
            }
        ]
        mock_garth.activities.return_value = invalid_activities

        result = get_activities_typed("2025-11-16")

        # Should return raw data
        assert result == invalid_activities
        # Should log warning about validation
        mock_logger.warning.assert_called_once()

    @patch("app.services.garth_wrapper.garth")
    def test_get_daily_summary_typed_valid(self, mock_garth):
        """get_daily_summary_typed should return summary when valid."""
        valid_summary = {
            "calendarDate": "2025-11-16",
            "steps": 10000,
            "distanceMeters": 8000,
            "activeCalories": 500,
        }
        mock_garth.daily_summary.return_value = valid_summary

        result = get_daily_summary_typed("2025-11-16")

        assert result == valid_summary
        mock_garth.daily_summary.assert_called_once_with("2025-11-16")

    @patch("app.services.garth_wrapper.garth")
    @patch("app.services.garth_wrapper.logger")
    def test_get_daily_summary_typed_missing_fields(self, mock_logger, mock_garth):
        """get_daily_summary_typed should warn but return data when fields missing."""
        # DailyMetrics requires at least date, other fields are optional
        minimal_summary = {
            "calendarDate": "2025-11-16",
        }
        mock_garth.daily_summary.return_value = minimal_summary

        result = get_daily_summary_typed("2025-11-16")

        # Should return raw data
        assert result == minimal_summary
        # Validation should pass (all fields except date are optional)

    @patch("app.services.garth_wrapper.garth")
    def test_get_health_snapshot_typed_valid(self, mock_garth):
        """get_health_snapshot_typed should return snapshot when valid."""
        valid_snapshot = {
            "heartRate": 72,
            "respirationRate": 15,
            "stressLevel": 25,
            "spo2": 98,
        }
        mock_garth.health_snapshot.return_value = valid_snapshot

        result = get_health_snapshot_typed()

        assert result == valid_snapshot
        mock_garth.health_snapshot.assert_called_once()

    @patch("app.services.garth_wrapper.garth")
    def test_get_health_snapshot_typed_missing_fields(self, mock_garth):
        """get_health_snapshot_typed should handle missing optional fields."""
        minimal_snapshot = {}
        mock_garth.health_snapshot.return_value = minimal_snapshot

        result = get_health_snapshot_typed()

        # Should return raw data
        assert result == minimal_snapshot

    @patch("app.services.garth_wrapper.garth")
    def test_get_user_profile_typed_valid(self, mock_garth):
        """get_user_profile_typed should return profile when valid."""
        valid_profile = {
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
        }
        mock_garth.client.profile = valid_profile

        result = get_user_profile_typed()

        assert result == valid_profile

    @patch("app.services.garth_wrapper.garth")
    def test_get_user_profile_typed_missing_display_name(self, mock_garth):
        """get_user_profile_typed should handle optional displayName field."""
        minimal_profile = {
            "emailAddress": "john@example.com",
        }
        mock_garth.client.profile = minimal_profile

        result = get_user_profile_typed()

        # Should return raw data (displayName is optional)
        assert result == minimal_profile
