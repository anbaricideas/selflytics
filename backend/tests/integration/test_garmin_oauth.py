"""Integration tests for Garmin OAuth and service layer."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.garmin_data import GarminActivity
from app.services.garmin_service import GarminService


@pytest.fixture
def mock_garmin_client():
    """Mock GarminClient for testing."""
    with patch("app.services.garmin_service.GarminClient") as mock_client_class:
        mock_client = Mock()
        mock_client.authenticate = AsyncMock(return_value=True)
        mock_client.get_activities = AsyncMock(return_value=[])
        mock_client.load_tokens = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_cache():
    """Mock GarminDataCache for testing."""
    with patch("app.services.garmin_service.GarminDataCache") as mock_cache_class:
        mock_cache_instance = Mock()
        mock_cache_instance.get = AsyncMock(return_value=None)
        mock_cache_instance.set = AsyncMock()
        mock_cache_class.return_value = mock_cache_instance
        yield mock_cache_instance


@pytest.fixture
def mock_user_service():
    """Mock UserService for testing."""
    with patch("app.services.garmin_service.UserService") as mock_service_class:
        mock_service = Mock()
        mock_service.update_garmin_status = AsyncMock()
        mock_service_class.return_value = mock_service
        yield mock_service


class TestLinkAccount:
    """Tests for linking Garmin account to user."""

    @pytest.mark.asyncio
    async def test_link_account_success(self, mock_garmin_client, mock_cache, mock_user_service):
        """Test successful account linking."""
        service = GarminService("user123")

        result = await service.link_account("test@example.com", "password123")

        assert result is True
        mock_garmin_client.authenticate.assert_called_once_with("test@example.com", "password123")
        mock_user_service.update_garmin_status.assert_called_once_with(
            user_id="user123", linked=True
        )

    @pytest.mark.asyncio
    async def test_link_account_auth_failure(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test account linking with authentication failure."""
        mock_garmin_client.authenticate = AsyncMock(return_value=False)

        service = GarminService("user123")
        result = await service.link_account("test@example.com", "wrong_password")

        assert result is False
        mock_garmin_client.authenticate.assert_called_once()
        # Should not update user status on failure
        mock_user_service.update_garmin_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_link_account_triggers_sync(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test that linking account triggers initial data sync."""
        service = GarminService("user123")

        # Mock activities returned from sync
        mock_activities = [
            GarminActivity(
                activity_id=123,
                activity_name="Morning Run",
                activity_type="running",
                start_time_local=datetime.now(UTC),
            )
        ]
        mock_garmin_client.get_activities = AsyncMock(return_value=mock_activities)

        result = await service.link_account("test@example.com", "password123")

        assert result is True
        # Should fetch activities after linking
        mock_garmin_client.get_activities.assert_called_once()
        # Should cache the activities
        mock_cache.set.assert_called_once()


class TestSyncRecentData:
    """Tests for syncing recent Garmin data."""

    @pytest.mark.asyncio
    async def test_sync_recent_data_30_days(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test syncing last 30 days of activities."""
        service = GarminService("user123")

        mock_activities = [
            GarminActivity(
                activity_id=123,
                activity_name="Run",
                activity_type="running",
                start_time_local=datetime.now(UTC),
            ),
            GarminActivity(
                activity_id=124,
                activity_name="Bike",
                activity_type="cycling",
                start_time_local=datetime.now(UTC),
            ),
        ]
        mock_garmin_client.get_activities = AsyncMock(return_value=mock_activities)

        await service.sync_recent_data()

        # Verify called with correct date range (30 days)
        call_args = mock_garmin_client.get_activities.call_args
        start_date, end_date = call_args[0]

        assert isinstance(start_date, date)
        assert isinstance(end_date, date)
        assert end_date == date.today()
        assert (end_date - start_date).days == 30

    @pytest.mark.asyncio
    async def test_sync_caches_activities(self, mock_garmin_client, mock_cache, mock_user_service):
        """Test that sync caches the fetched activities."""
        service = GarminService("user123")

        mock_activities = [
            GarminActivity(
                activity_id=123,
                activity_name="Run",
                activity_type="running",
                start_time_local=datetime.now(UTC),
            )
        ]
        mock_garmin_client.get_activities = AsyncMock(return_value=mock_activities)

        await service.sync_recent_data()

        # Should cache activities
        mock_cache.set.assert_called_once()
        cache_call = mock_cache.set.call_args
        assert cache_call.kwargs["user_id"] == "user123"
        assert cache_call.kwargs["data_type"] == "activities"
        assert len(cache_call.kwargs["data"]) == 1

    @pytest.mark.asyncio
    async def test_sync_empty_activities(self, mock_garmin_client, mock_cache, mock_user_service):
        """Test syncing when no activities are returned."""
        service = GarminService("user123")

        mock_garmin_client.get_activities = AsyncMock(return_value=[])

        await service.sync_recent_data()

        # Should still cache empty result
        mock_cache.set.assert_called_once()
        cache_call = mock_cache.set.call_args
        assert cache_call.kwargs["data"] == []


class TestGetActivitiesCached:
    """Tests for getting activities with caching."""

    @pytest.mark.asyncio
    async def test_get_activities_cache_hit(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test getting activities from cache (cache hit)."""
        service = GarminService("user123")

        # Mock cached data
        cached_activities = [
            {"activity_id": 123, "activity_name": "Run", "activity_type": "running"}
        ]
        mock_cache.get = AsyncMock(return_value=cached_activities)

        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        result = await service.get_activities_cached(start_date, end_date)

        assert result == cached_activities
        # Should check cache
        mock_cache.get.assert_called_once()
        # Should NOT call Garmin API
        mock_garmin_client.get_activities.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_activities_cache_miss(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test getting activities from API (cache miss)."""
        service = GarminService("user123")

        # Mock cache miss
        mock_cache.get = AsyncMock(return_value=None)

        # Mock API response
        mock_activities = [
            GarminActivity(
                activity_id=123,
                activity_name="Run",
                activity_type="running",
                start_time_local=datetime.now(UTC),
            )
        ]
        mock_garmin_client.get_activities = AsyncMock(return_value=mock_activities)

        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        result = await service.get_activities_cached(start_date, end_date)

        # Should fetch from API
        mock_garmin_client.get_activities.assert_called_once_with(start_date, end_date)
        # Should cache the result
        mock_cache.set.assert_called_once()
        # Should return serialized activities
        assert len(result) == 1
        assert result[0]["activity_id"] == 123

    @pytest.mark.asyncio
    async def test_get_activities_cache_key_includes_date_range(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test that cache key includes the date range."""
        service = GarminService("user123")

        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        await service.get_activities_cached(start_date, end_date)

        # Verify cache.get was called with correct parameters
        cache_call = mock_cache.get.call_args
        assert cache_call.kwargs["user_id"] == "user123"
        assert cache_call.kwargs["data_type"] == "activities"
        assert "date_range" in cache_call.kwargs
        assert "2025-01-01" in cache_call.kwargs["date_range"]
        assert "2025-01-31" in cache_call.kwargs["date_range"]


class TestErrorHandling:
    """Tests for error handling in GarminService."""

    @pytest.mark.asyncio
    async def test_sync_handles_client_error(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test sync handles GarminClient errors gracefully."""
        service = GarminService("user123")

        mock_garmin_client.get_activities = AsyncMock(side_effect=Exception("Garmin API error"))

        # Should raise the exception (caller can handle)
        with pytest.raises(Exception, match="Garmin API error"):
            await service.sync_recent_data()

    @pytest.mark.asyncio
    async def test_get_activities_handles_cache_error(
        self, mock_garmin_client, mock_cache, mock_user_service
    ):
        """Test get_activities handles cache errors gracefully."""
        service = GarminService("user123")

        # Mock cache error
        mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))

        # Mock API response as fallback
        mock_activities = [
            GarminActivity(
                activity_id=123,
                activity_name="Run",
                activity_type="running",
                start_time_local=datetime.now(UTC),
            )
        ]
        mock_garmin_client.get_activities = AsyncMock(return_value=mock_activities)

        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        result = await service.get_activities_cached(start_date, end_date)

        # Should fetch from API despite cache error
        mock_garmin_client.get_activities.assert_called_once()
        assert len(result) == 1
