"""Tests for Garmin data caching utilities."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from app.utils.cache import GarminDataCache


@pytest.fixture
def mock_firestore():
    """Mock Firestore client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_db.collection.return_value = mock_collection
    return mock_db, mock_collection


@pytest.fixture
def cache(mock_firestore, monkeypatch):
    """Create cache instance with mocked Firestore."""
    mock_db, _mock_collection = mock_firestore

    # Mock get_firestore_client to return our mock
    def mock_get_firestore_client():
        return mock_db

    monkeypatch.setattr("app.utils.cache.get_firestore_client", mock_get_firestore_client)

    return GarminDataCache()


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_cache_key_basic(self, cache):
        """Test basic cache key generation."""
        key = cache._cache_key("user123", "activities")
        assert key == "user123:activities"

    def test_cache_key_with_kwargs(self, cache):
        """Test cache key with additional parameters."""
        key = cache._cache_key("user123", "activities", date_range="2025-01-01:2025-01-31")
        assert key == "user123:activities:date_range:2025-01-01:2025-01-31"

    def test_cache_key_sorted_kwargs(self, cache):
        """Test cache key kwargs are sorted for consistency."""
        key1 = cache._cache_key("user123", "activities", start="2025-01-01", end="2025-01-31")
        key2 = cache._cache_key("user123", "activities", end="2025-01-31", start="2025-01-01")
        assert key1 == key2

    def test_cache_key_multiple_kwargs(self, cache):
        """Test cache key with multiple kwargs."""
        key = cache._cache_key(
            "user456", "daily_metrics", date="2025-01-15", metric_type="heart_rate"
        )
        assert "user456" in key
        assert "daily_metrics" in key
        assert "date:2025-01-15" in key
        assert "metric_type:heart_rate" in key

    def test_cache_key_uniqueness(self, cache):
        """Test cache keys are unique for different parameter combinations."""
        key1 = cache._cache_key("user1", "activities", date="2025-01-01")
        key2 = cache._cache_key("user2", "activities", date="2025-01-01")
        key3 = cache._cache_key("user1", "metrics", date="2025-01-01")
        key4 = cache._cache_key("user1", "activities", date="2025-01-02")

        keys = [key1, key2, key3, key4]
        assert len(keys) == len(set(keys)), "All keys should be unique"


class TestCacheSave:
    """Tests for saving data to cache."""

    @pytest.mark.asyncio
    async def test_set_basic(self, cache, mock_firestore):
        """Test saving data to cache."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = {"activity_id": 123, "name": "Morning Run"}
        await cache.set("user123", "activities", data, date_range="2025-01-01:2025-01-31")

        # Verify document was saved
        mock_collection.document.assert_called_once()
        mock_doc.set.assert_called_once()

        # Check saved data structure
        saved_data = mock_doc.set.call_args[0][0]
        assert saved_data["user_id"] == "user123"
        assert saved_data["data_type"] == "activities"
        assert saved_data["data"] == data
        assert "cached_at" in saved_data
        assert "expires_at" in saved_data
        assert "cache_key" in saved_data

    @pytest.mark.asyncio
    async def test_set_with_default_ttl_activities(self, cache, mock_firestore):
        """Test TTL defaults to 24 hours for activities."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = {"activity_id": 123}
        before = datetime.utcnow()
        await cache.set("user123", "activities", data)
        after = datetime.utcnow()

        saved_data = mock_doc.set.call_args[0][0]
        expires_at = saved_data["expires_at"]

        # Should expire ~24 hours from now
        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24)
        assert expected_min <= expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_set_with_default_ttl_metrics(self, cache, mock_firestore):
        """Test TTL defaults to 6 hours for daily_metrics."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = {"steps": 10000}
        before = datetime.utcnow()
        await cache.set("user123", "daily_metrics", data)
        after = datetime.utcnow()

        saved_data = mock_doc.set.call_args[0][0]
        expires_at = saved_data["expires_at"]

        # Should expire ~6 hours from now
        expected_min = before + timedelta(hours=6)
        expected_max = after + timedelta(hours=6)
        assert expected_min <= expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_set_with_default_ttl_health(self, cache, mock_firestore):
        """Test TTL defaults to 1 hour for health_snapshot."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = {"heart_rate": 72}
        before = datetime.utcnow()
        await cache.set("user123", "health_snapshot", data)
        after = datetime.utcnow()

        saved_data = mock_doc.set.call_args[0][0]
        expires_at = saved_data["expires_at"]

        # Should expire ~1 hour from now
        expected_min = before + timedelta(hours=1)
        expected_max = after + timedelta(hours=1)
        assert expected_min <= expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache, mock_firestore):
        """Test setting custom TTL."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = {"test": "data"}
        custom_ttl = timedelta(minutes=30)
        before = datetime.utcnow()
        await cache.set("user123", "custom_type", data, ttl=custom_ttl)
        after = datetime.utcnow()

        saved_data = mock_doc.set.call_args[0][0]
        expires_at = saved_data["expires_at"]

        # Should expire ~30 minutes from now
        expected_min = before + timedelta(minutes=30)
        expected_max = after + timedelta(minutes=30)
        assert expected_min <= expires_at <= expected_max


class TestCacheLoad:
    """Tests for loading data from cache."""

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache, mock_firestore):
        """Test loading data from cache (cache hit)."""
        _, mock_collection = mock_firestore
        mock_doc_ref = Mock()
        mock_doc_snapshot = Mock()
        mock_doc_snapshot.exists = True

        # Mock cached data (not expired)
        cached_data = {
            "user_id": "user123",
            "data_type": "activities",
            "data": [{"activity_id": 123, "name": "Morning Run"}],
            "cached_at": datetime.utcnow() - timedelta(hours=1),
            "expires_at": datetime.utcnow() + timedelta(hours=23),
            "cache_key": "user123:activities",
        }
        mock_doc_snapshot.to_dict.return_value = cached_data
        mock_doc_ref.get.return_value = mock_doc_snapshot
        mock_collection.document.return_value = mock_doc_ref

        result = await cache.get("user123", "activities")

        assert result is not None
        assert result == cached_data["data"]
        mock_collection.document.assert_called_once()
        mock_doc_ref.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_miss_not_exists(self, cache, mock_firestore):
        """Test cache miss when document doesn't exist."""
        _, mock_collection = mock_firestore
        mock_doc_ref = Mock()
        mock_doc_snapshot = Mock()
        mock_doc_snapshot.exists = False
        mock_doc_ref.get.return_value = mock_doc_snapshot
        mock_collection.document.return_value = mock_doc_ref

        result = await cache.get("user123", "activities")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cache_miss_expired(self, cache, mock_firestore):
        """Test cache miss when data is expired."""
        _, mock_collection = mock_firestore
        mock_doc_ref = Mock()
        mock_doc_snapshot = Mock()
        mock_doc_snapshot.exists = True

        # Mock expired cached data
        cached_data = {
            "user_id": "user123",
            "data_type": "activities",
            "data": [{"activity_id": 123}],
            "cached_at": datetime.utcnow() - timedelta(hours=25),
            "expires_at": datetime.utcnow() - timedelta(hours=1),  # Expired
            "cache_key": "user123:activities",
        }
        mock_doc_snapshot.to_dict.return_value = cached_data
        mock_doc_ref.get.return_value = mock_doc_snapshot
        mock_collection.document.return_value = mock_doc_ref

        result = await cache.get("user123", "activities")

        # Should return None for expired data
        assert result is None

        # Should delete expired document
        mock_doc_ref.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_with_kwargs(self, cache, mock_firestore):
        """Test loading cached data with kwargs."""
        _, mock_collection = mock_firestore
        mock_doc_ref = Mock()
        mock_doc_snapshot = Mock()
        mock_doc_snapshot.exists = True

        cached_data = {
            "user_id": "user123",
            "data_type": "activities",
            "data": [{"activity_id": 123}],
            "cached_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "cache_key": "user123:activities:date_range:2025-01-01:2025-01-31",
        }
        mock_doc_snapshot.to_dict.return_value = cached_data
        mock_doc_ref.get.return_value = mock_doc_snapshot
        mock_collection.document.return_value = mock_doc_ref

        result = await cache.get("user123", "activities", date_range="2025-01-01:2025-01-31")

        assert result is not None
        assert result == cached_data["data"]


class TestCacheInvalidation:
    """Tests for cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_specific_type(self, cache, mock_firestore):
        """Test invalidating specific data type for user."""
        _, mock_collection = mock_firestore

        # Mock query results
        mock_doc1 = Mock()
        mock_doc1.reference = Mock()
        mock_doc2 = Mock()
        mock_doc2.reference = Mock()

        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc1, mock_doc2]

        # Create intermediate mock for chained where calls
        mock_where1 = Mock()
        mock_where1.where.return_value = mock_query
        mock_collection.where.return_value = mock_where1

        await cache.invalidate("user123", data_type="activities")

        # Verify both where clauses were called
        mock_collection.where.assert_called_once_with("user_id", "==", "user123")
        mock_where1.where.assert_called_once_with("data_type", "==", "activities")

        # Verify documents were deleted
        mock_doc1.reference.delete.assert_called_once()
        mock_doc2.reference.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_all_types(self, cache, mock_firestore):
        """Test invalidating all cached data for user."""
        _, mock_collection = mock_firestore

        # Mock query results
        mock_doc1 = Mock()
        mock_doc1.reference = Mock()
        mock_doc2 = Mock()
        mock_doc2.reference = Mock()
        mock_doc3 = Mock()
        mock_doc3.reference = Mock()

        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc1, mock_doc2, mock_doc3]
        mock_collection.where.return_value = mock_query

        await cache.invalidate("user123")

        # Verify query was made (only one where clause for user_id)
        mock_collection.where.assert_called_once_with("user_id", "==", "user123")

        # Verify all documents were deleted
        mock_doc1.reference.delete.assert_called_once()
        mock_doc2.reference.delete.assert_called_once()
        mock_doc3.reference.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_no_cached_data(self, cache, mock_firestore):
        """Test invalidation when no cached data exists."""
        _, mock_collection = mock_firestore

        mock_query = Mock()
        mock_query.stream.return_value = []  # No documents
        mock_collection.where.return_value = mock_query

        # Should not raise an error
        await cache.invalidate("user123")

        mock_collection.where.assert_called_once()


class TestErrorHandling:
    """Tests for error handling in cache operations."""

    @pytest.mark.asyncio
    async def test_get_firestore_error(self, cache, mock_firestore):
        """Test cache get handles Firestore errors gracefully."""
        _, mock_collection = mock_firestore
        mock_doc_ref = Mock()
        mock_doc_ref.get.side_effect = Exception("Firestore unavailable")
        mock_collection.document.return_value = mock_doc_ref

        # Should return None on error rather than raising
        result = await cache.get("user123", "activities")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_firestore_error(self, cache, mock_firestore):
        """Test cache set handles Firestore errors gracefully."""
        _, mock_collection = mock_firestore
        mock_doc_ref = Mock()
        mock_doc_ref.set.side_effect = Exception("Firestore unavailable")
        mock_collection.document.return_value = mock_doc_ref

        data = {"activity_id": 123}

        # Should raise exception to caller (write failures are critical)
        with pytest.raises(Exception, match="Firestore unavailable"):
            await cache.set("user123", "activities", data)

    @pytest.mark.asyncio
    async def test_invalidate_firestore_error(self, cache, mock_firestore):
        """Test cache invalidation handles Firestore errors gracefully."""
        _, mock_collection = mock_firestore
        mock_query = Mock()
        mock_query.stream.side_effect = Exception("Firestore unavailable")
        mock_collection.where.return_value = mock_query

        # Should not raise error during invalidation
        # (invalidation failures are non-critical)
        try:
            await cache.invalidate("user123")
        except Exception:
            pytest.fail("Invalidation should handle Firestore errors gracefully")


class TestDataSerialization:
    """Tests for data serialization in cache."""

    @pytest.mark.asyncio
    async def test_set_with_dict_data(self, cache, mock_firestore):
        """Test caching dict data directly."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = {"activity_id": 123, "name": "Morning Run"}
        await cache.set("user123", "activities", data)

        # Verify data was stored as dict
        saved_data = mock_doc.set.call_args[0][0]
        assert saved_data["data"] == data
        assert isinstance(saved_data["data"], dict)

    @pytest.mark.asyncio
    async def test_set_with_list_data(self, cache, mock_firestore):
        """Test caching list of dicts."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = [
            {"activity_id": 123, "name": "Morning Run"},
            {"activity_id": 124, "name": "Evening Bike"},
        ]
        await cache.set("user123", "activities", data)

        # Verify data was stored as list
        saved_data = mock_doc.set.call_args[0][0]
        assert saved_data["data"] == data
        assert isinstance(saved_data["data"], list)

    @pytest.mark.asyncio
    async def test_set_with_empty_data(self, cache, mock_firestore):
        """Test caching empty data structures."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        # Empty list
        await cache.set("user123", "activities", [])
        saved_data = mock_doc.set.call_args[0][0]
        assert saved_data["data"] == []

        # Empty dict
        await cache.set("user123", "metrics", {})
        saved_data = mock_doc.set.call_args[0][0]
        assert saved_data["data"] == {}


class TestTTLBoundaries:
    """Tests for TTL boundary conditions."""

    @pytest.mark.asyncio
    async def test_get_cache_expired_exactly_now(self, cache, mock_firestore):
        """Test cache expiration at exact boundary (expires_at == now)."""
        _, mock_collection = mock_firestore
        mock_doc_ref = Mock()
        mock_doc_snapshot = Mock()
        mock_doc_snapshot.exists = True

        # Expired exactly now
        now = datetime.utcnow()
        cached_data = {
            "user_id": "user123",
            "data_type": "activities",
            "data": [{"activity_id": 123}],
            "cached_at": now - timedelta(hours=1),
            "expires_at": now,  # Exact match
            "cache_key": "user123:activities",
        }
        mock_doc_snapshot.to_dict.return_value = cached_data
        mock_doc_ref.get.return_value = mock_doc_snapshot
        mock_collection.document.return_value = mock_doc_ref

        result = await cache.get("user123", "activities")

        # Should treat as expired (>= comparison)
        assert result is None
        mock_doc_ref.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_with_zero_ttl(self, cache, mock_firestore):
        """Test setting TTL to zero (immediate expiration)."""
        _, mock_collection = mock_firestore
        mock_doc = Mock()
        mock_collection.document.return_value = mock_doc

        data = {"test": "data"}
        await cache.set("user123", "test", data, ttl=timedelta(seconds=0))

        saved_data = mock_doc.set.call_args[0][0]
        # expires_at should be approximately now (within 1 second)
        expires_at = saved_data["expires_at"]
        now = datetime.utcnow()
        assert abs((expires_at - now).total_seconds()) < 1
