"""Unit tests for GarminService.get_user_profile method."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.garmin_service import GarminService


class TestGarminServiceUserProfile:
    """Test GarminService.get_user_profile method."""

    @pytest.fixture
    def garmin_service(self):
        """Create GarminService instance for testing."""
        service = GarminService(user_id="test_user_123")
        # Mock load_tokens to avoid actual Firestore calls
        service.client.load_tokens = AsyncMock(return_value=True)
        return service

    @patch("app.services.garmin_client.garth.client")
    @pytest.mark.asyncio
    async def test_get_user_profile_returns_display_name(self, mock_garth_client, garmin_service):
        """Test that get_user_profile returns display name from garth.client.profile."""
        # Arrange
        mock_garth_client.profile = {"displayName": "John Doe", "fullName": "John Smith Doe"}

        # Act
        profile = await garmin_service.get_user_profile()

        # Assert
        assert profile["display_name"] == "John Doe"
        garmin_service.client.load_tokens.assert_called_once()

    @patch("app.services.garmin_client.garth.client")
    @pytest.mark.asyncio
    async def test_get_user_profile_handles_missing_display_name(
        self, mock_garth_client, garmin_service
    ):
        """Test that get_user_profile handles missing displayName gracefully."""
        # Arrange
        mock_garth_client.profile = {"fullName": "Jane Doe"}

        # Act
        profile = await garmin_service.get_user_profile()

        # Assert
        assert profile["display_name"] == "User"  # Default value

    @patch("app.services.garmin_client.garth.client")
    @pytest.mark.asyncio
    async def test_get_user_profile_handles_empty_profile(self, mock_garth_client, garmin_service):
        """Test that get_user_profile handles empty profile dict."""
        # Arrange
        mock_garth_client.profile = {}

        # Act
        profile = await garmin_service.get_user_profile()

        # Assert
        assert profile["display_name"] == "User"  # Default value

    @patch("app.services.garmin_client.garth.client")
    @pytest.mark.asyncio
    async def test_get_user_profile_returns_dict_with_expected_keys(
        self, mock_garth_client, garmin_service
    ):
        """Test that get_user_profile returns dict with expected structure."""
        # Arrange
        mock_garth_client.profile = {"displayName": "Test User"}

        # Act
        profile = await garmin_service.get_user_profile()

        # Assert
        assert isinstance(profile, dict)
        assert "display_name" in profile
