"""Tests for Pydantic-AI chat tools."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.prompts.chat_agent import (
    garmin_activity_tool,
    garmin_metrics_tool,
    garmin_profile_tool,
)


class TestGarminActivityTool:
    """Test garmin_activity_tool."""

    @pytest.mark.asyncio
    async def test_get_activities_basic(self):
        """Test fetching activities with mock service."""
        # Mock context with user_id
        ctx = MagicMock()
        ctx.deps = "user-123"

        # Mock activities data
        mock_activities = [
            {
                "start_time_local": "2025-01-10T06:00:00",
                "activity_type": "running",
                "distance_meters": 5000,
                "duration_seconds": 1800,
                "average_hr": 145,
                "calories": 350,
            },
            {
                "start_time_local": "2025-01-11T07:00:00",
                "activity_type": "cycling",
                "distance_meters": 20000,
                "duration_seconds": 3600,
                "average_hr": 135,
                "calories": 600,
            },
        ]

        # Patch GarminService
        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_activities_cached.return_value = mock_activities
            mock_service_class.return_value = mock_service

            result = await garmin_activity_tool(ctx, start_date="2025-01-10", end_date="2025-01-11")

            # Verify service was called correctly
            mock_service_class.assert_called_once_with("user-123")
            mock_service.get_activities_cached.assert_called_once()
            args = mock_service.get_activities_cached.call_args[0]
            assert args[0] == date(2025, 1, 10)
            assert args[1] == date(2025, 1, 11)

            # Verify result format
            assert result["total_count"] == 2
            assert result["date_range"] == "2025-01-10 to 2025-01-11"
            assert len(result["activities"]) == 2

            # Check first activity
            activity = result["activities"][0]
            assert activity["type"] == "running"
            assert activity["distance_km"] == 5.0
            assert activity["duration_min"] == 30.0
            assert activity["avg_hr"] == 145

    @pytest.mark.asyncio
    async def test_get_activities_with_type_filter(self):
        """Test filtering activities by type."""
        ctx = MagicMock()
        ctx.deps = "user-123"

        mock_activities = [
            {"activity_type": "running", "distance_meters": 5000, "duration_seconds": 1800},
            {"activity_type": "cycling", "distance_meters": 20000, "duration_seconds": 3600},
            {"activity_type": "running", "distance_meters": 8000, "duration_seconds": 2400},
        ]

        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_activities_cached.return_value = mock_activities
            mock_service_class.return_value = mock_service

            result = await garmin_activity_tool(
                ctx,
                start_date="2025-01-10",
                end_date="2025-01-12",
                activity_type="running",
            )

            # Should only return running activities
            assert result["total_count"] == 2
            assert len(result["activities"]) == 2
            assert all(a["type"] == "running" for a in result["activities"])

    @pytest.mark.asyncio
    async def test_get_activities_limit_50(self):
        """Test that activities are limited to 50 for token efficiency."""
        ctx = MagicMock()
        ctx.deps = "user-123"

        # Create 60 mock activities
        mock_activities = [
            {
                "activity_type": "running",
                "distance_meters": 5000,
                "duration_seconds": 1800,
            }
            for _ in range(60)
        ]

        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_activities_cached.return_value = mock_activities
            mock_service_class.return_value = mock_service

            result = await garmin_activity_tool(ctx, start_date="2025-01-01", end_date="2025-01-31")

            # Total count should be 60, but activities list limited to 50
            assert result["total_count"] == 60
            assert len(result["activities"]) == 50


class TestGarminMetricsTool:
    """Test garmin_metrics_tool."""

    @pytest.mark.asyncio
    async def test_get_steps_metrics(self):
        """Test fetching steps metrics."""
        ctx = MagicMock()
        ctx.deps = "user-123"

        # Mock to return steps data for any date
        mock_metrics = {"steps": 8500, "resting_heart_rate": 58}

        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_daily_metrics_cached.return_value = mock_metrics
            mock_service_class.return_value = mock_service

            result = await garmin_metrics_tool(ctx, metric_type="steps", days=2)

            # Verify result - should have 3 days worth (today, yesterday, day before)
            assert result["metric_type"] == "steps"
            assert result["days"] == 2
            assert result["unit"] == "steps/day"
            # Should have 3 data points (start_date to end_date inclusive)
            assert len(result["data"]) == 3
            assert result["average"] == 8500  # All same value
            # Verify all data points have the value
            assert all(d["value"] == 8500 for d in result["data"])

    @pytest.mark.asyncio
    async def test_get_sleep_metrics(self):
        """Test fetching sleep metrics (converted to hours)."""
        ctx = MagicMock()
        ctx.deps = "user-123"

        mock_metrics = {"sleep_seconds": 28800}  # 8 hours

        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_daily_metrics_cached.return_value = mock_metrics
            mock_service_class.return_value = mock_service

            result = await garmin_metrics_tool(ctx, metric_type="sleep", days=1)

            assert result["metric_type"] == "sleep"
            assert result["unit"] == "hours"
            # 28800 seconds = 8 hours
            assert result["data"][0]["value"] == 8.0

    @pytest.mark.asyncio
    async def test_get_metrics_with_missing_data(self):
        """Test handling missing data gracefully."""
        from google.api_core.exceptions import GoogleAPIError

        ctx = MagicMock()
        ctx.deps = "user-123"

        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            # Simulate Firestore exception for missing data (more specific than generic Exception)
            mock_service.get_daily_metrics_cached.side_effect = GoogleAPIError("No data")
            mock_service_class.return_value = mock_service

            result = await garmin_metrics_tool(ctx, metric_type="steps", days=2)

            # Should return empty data list but not crash
            assert result["data"] == []
            assert result["average"] == 0


class TestGarminProfileTool:
    """Test garmin_profile_tool."""

    @pytest.mark.asyncio
    async def test_get_user_profile(self):
        """Test fetching user profile."""
        ctx = MagicMock()
        ctx.deps = "user-123"

        mock_profile = {"display_name": "John Runner", "email": "john@example.com"}

        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user_profile.return_value = mock_profile
            mock_service_class.return_value = mock_service

            result = await garmin_profile_tool(ctx)

            # Verify result (email removed to reduce PII exposure)
            assert result["display_name"] == "John Runner"
            assert "email" not in result  # Email no longer exposed to AI agent
            assert result["garmin_linked"] is True

    @pytest.mark.asyncio
    async def test_get_profile_missing_fields(self):
        """Test profile with missing optional fields."""
        ctx = MagicMock()
        ctx.deps = "user-123"

        mock_profile = {}  # Empty profile

        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_user_profile.return_value = mock_profile
            mock_service_class.return_value = mock_service

            result = await garmin_profile_tool(ctx)

            # Should use defaults (email no longer returned)
            assert result["display_name"] == "User"
            assert "email" not in result  # Email no longer exposed to AI agent
            assert result["garmin_linked"] is True
