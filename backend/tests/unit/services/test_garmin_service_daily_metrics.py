"""
Unit tests for GarminService.get_daily_metrics_cached method.

These tests verify the caching pattern for daily metrics retrieval,
ensuring it follows the same pattern as get_activities_cached.

Context: Bug #8 - get_daily_metrics_cached method missing from GarminService
"""

# Commented code documents post-fix assertions in TDD

from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.models.garmin_data import DailyMetrics
from app.services.garmin_service import GarminService


@pytest.mark.asyncio
async def test_get_daily_metrics_cached_method_exists():
    """
    GarminService should have get_daily_metrics_cached method.

    Expected: Method exists and is callable
    Context: Bug #8 - method was completely missing (now fixed)
    """
    service = GarminService(user_id="test-user")
    target_date = date.today()

    # Mock dependencies to prevent actual API calls
    service.cache = AsyncMock()
    service.cache.get.return_value = {"steps": 10000}
    service.client = AsyncMock()

    assert hasattr(service, "get_daily_metrics_cached")
    assert callable(service.get_daily_metrics_cached)
    result = await service.get_daily_metrics_cached(target_date)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_daily_metrics_cached_returns_cached_data():
    """
    get_daily_metrics_cached should return cached data when available.

    Expected: Returns cached dict without calling Garmin API
    Context: Cache hit path should be efficient (no API calls)
    """
    service = GarminService(user_id="test-user-123")
    target_date = date(2025, 11, 14)

    # Mock cached data
    cached_metrics = {
        "steps": 12000,
        "resting_heart_rate": 58,
        "sleep_seconds": 27000,
        "avg_stress_level": 25,
    }

    # Mock cache.get to return data
    service.cache = AsyncMock()
    service.cache.get.return_value = cached_metrics

    result = await service.get_daily_metrics_cached(target_date)

    assert result == cached_metrics
    assert not hasattr(result, "model_dump"), "Should return dict, not Pydantic model"
    service.cache.get.assert_called_once_with(
        user_id="test-user-123", data_type="daily_metrics", date_range=str(target_date)
    )


@pytest.mark.asyncio
async def test_get_daily_metrics_cached_fetches_from_api_on_cache_miss():
    """
    get_daily_metrics_cached should fetch from Garmin API on cache miss.

    Expected: Calls GarminClient.get_daily_summary when cache empty
    Context: Cache miss path should fallback to API gracefully
    """
    service = GarminService(user_id="test-user-123")
    target_date = date(2025, 11, 14)

    # Mock cache miss
    service.cache = AsyncMock()
    service.cache.get.return_value = None

    # Mock Garmin API response
    mock_metrics = DailyMetrics(
        date=target_date,
        steps=15000,
        resting_heart_rate=62,
        sleep_seconds=28800,
        avg_stress_level=35,
    )
    service.client = AsyncMock()
    service.client.get_daily_metrics.return_value = mock_metrics

    result = await service.get_daily_metrics_cached(target_date)

    assert result["steps"] == 15000
    assert result["resting_heart_rate"] == 62
    assert isinstance(result, dict), "Should return dict, not Pydantic model"
    service.client.get_daily_metrics.assert_called_once_with(target_date)


@pytest.mark.asyncio
async def test_get_daily_metrics_cached_caches_api_results():
    """
    get_daily_metrics_cached should cache API results after fetch.

    Expected: Calls cache.set with fetched data
    Context: Future requests should hit cache, not API
    """
    service = GarminService(user_id="test-user-123")
    target_date = date(2025, 11, 14)

    # Mock cache miss
    service.cache = AsyncMock()
    service.cache.get.return_value = None

    # Mock API response
    mock_metrics = DailyMetrics(
        date=target_date,
        steps=15000,
        resting_heart_rate=62,
        sleep_seconds=28800,
        avg_stress_level=35,
    )
    service.client = AsyncMock()
    service.client.get_daily_metrics.return_value = mock_metrics

    await service.get_daily_metrics_cached(target_date)

    service.cache.set.assert_called_once()
    call_args = service.cache.set.call_args
    assert call_args.kwargs["user_id"] == "test-user-123"
    assert call_args.kwargs["data_type"] == "daily_metrics"
    assert call_args.kwargs["date_range"] == str(target_date)
    assert "steps" in call_args.kwargs["data"]


@pytest.mark.asyncio
async def test_get_daily_metrics_cached_handles_cache_errors_gracefully():
    """
    get_daily_metrics_cached should continue on cache errors.

    Expected: Falls back to API if cache.get raises exception
    Context: Cache failures should not break functionality
    """
    service = GarminService(user_id="test-user-123")
    target_date = date(2025, 11, 14)

    # Mock cache error
    service.cache = AsyncMock()
    service.cache.get.side_effect = Exception("Firestore timeout")

    # Mock API response
    mock_metrics = DailyMetrics(
        date=target_date,
        steps=10000,
        resting_heart_rate=60,
        sleep_seconds=25200,
        avg_stress_level=30,
    )
    service.client = AsyncMock()
    service.client.get_daily_metrics.return_value = mock_metrics

    result = await service.get_daily_metrics_cached(target_date)

    assert result["steps"] == 10000  # Should still return API data
    service.client.get_daily_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_get_daily_metrics_cached_returns_dict_format():
    """
    get_daily_metrics_cached should return dict, not Pydantic model.

    Expected: Returns dict with keys: steps, resting_heart_rate, sleep_seconds, avg_stress_level
    Context: AI agent tools expect dict format for easy manipulation
    """
    service = GarminService(user_id="test-user-123")
    target_date = date(2025, 11, 14)

    # Mock API response
    mock_metrics = DailyMetrics(
        date=target_date,
        steps=12500,
        resting_heart_rate=64,
        sleep_seconds=26100,
        avg_stress_level=28,
    )
    service.cache = AsyncMock()
    service.cache.get.return_value = None
    service.client = AsyncMock()
    service.client.get_daily_metrics.return_value = mock_metrics

    result = await service.get_daily_metrics_cached(target_date)

    assert isinstance(result, dict)
    assert "steps" in result
    assert "resting_heart_rate" in result
    assert "sleep_seconds" in result
    assert "avg_stress_level" in result
    assert result["steps"] == 12500
