"""Caching utilities for Garmin data."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from telemetry.logging_utils import redact_for_logging

from app.db.firestore_client import get_firestore_client


logger = logging.getLogger(__name__)


class GarminDataCache:
    """Cache for Garmin API responses in Firestore."""

    # TTL values
    TTL_ACTIVITIES = timedelta(hours=24)
    TTL_METRICS = timedelta(hours=6)
    TTL_HEALTH = timedelta(hours=1)

    def __init__(self) -> None:
        """Initialize cache with Firestore client."""
        self.db = get_firestore_client()
        self.collection = self.db.collection("garmin_data")

    def _cache_key(self, user_id: str, data_type: str, **kwargs: Any) -> str:
        """
        Generate cache key from user_id, data_type, and kwargs.

        Args:
            user_id: User identifier
            data_type: Type of data being cached
            **kwargs: Additional parameters for cache key

        Returns:
            Cache key string
        """
        parts = [user_id, data_type]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return ":".join(parts)

    async def get(self, user_id: str, data_type: str, **kwargs: Any) -> Any | None:
        """
        Get cached data if available and not expired.

        Args:
            user_id: User identifier
            data_type: Type of data to retrieve
            **kwargs: Additional parameters for cache key

        Returns:
            Cached data if available and not expired, None otherwise
        """
        try:
            cache_key = self._cache_key(user_id, data_type, **kwargs)

            # Wrap synchronous Firestore operation
            doc = await asyncio.to_thread(self.collection.document(cache_key).get)
            if not doc.exists:
                return None

            cached = doc.to_dict()

            # Check expiry
            expires_at = cached.get("expires_at")
            if expires_at and datetime.now(UTC) >= expires_at:
                # Expired - delete and return None (wrap synchronous operation)
                await asyncio.to_thread(self.collection.document(cache_key).delete)
                logger.debug("Cache expired and deleted: %s", cache_key)
                return None

            logger.debug("Cache hit: %s", cache_key)
            return cached.get("data")

        except Exception as e:
            logger.error("Cache get error: %s", redact_for_logging(str(e)))
            return None

    async def set(
        self, user_id: str, data_type: str, data: Any, ttl: timedelta | None = None, **kwargs: Any
    ) -> None:
        """
        Cache data with TTL.

        Args:
            user_id: User identifier
            data_type: Type of data being cached
            data: Data to cache (dict, list, or Pydantic model)
            ttl: Time to live (optional, uses defaults based on data_type)
            **kwargs: Additional parameters for cache key

        Raises:
            Exception: If Firestore write fails
        """
        cache_key = self._cache_key(user_id, data_type, **kwargs)

        # Determine TTL
        if ttl is None:
            if data_type == "activities":
                ttl = self.TTL_ACTIVITIES
            elif data_type == "daily_metrics":
                ttl = self.TTL_METRICS
            elif data_type == "health_snapshot":
                ttl = self.TTL_HEALTH
            else:
                ttl = timedelta(hours=1)

        expires_at = datetime.now(UTC) + ttl
        cached_at = datetime.now(UTC)

        # Serialize data (handles dict, list, Pydantic models)
        if isinstance(data, (dict, list)):
            serialized_data = data
        elif hasattr(data, "model_dump"):
            # Pydantic v2
            serialized_data = data.model_dump()
        elif hasattr(data, "dict"):
            # Pydantic v1
            serialized_data = data.dict()
        else:
            serialized_data = data

        # Save to Firestore (wrap synchronous operation)
        await asyncio.to_thread(
            self.collection.document(cache_key).set,
            {
                "user_id": user_id,
                "data_type": data_type,
                "data": serialized_data,
                "cached_at": cached_at,
                "expires_at": expires_at,
                "cache_key": cache_key,
            },
        )

        logger.debug("Cache set: %s (expires in %s)", cache_key, ttl)

    async def invalidate(self, user_id: str, data_type: str | None = None) -> None:
        """
        Invalidate cached data for user.

        Args:
            user_id: User identifier
            data_type: Optional data type to invalidate (all if None)
        """
        try:
            if data_type:
                # Invalidate specific type
                query = self.collection.where("user_id", "==", user_id).where(
                    "data_type", "==", data_type
                )
            else:
                # Invalidate all
                query = self.collection.where("user_id", "==", user_id)

            # Wrap synchronous Firestore operations
            docs = await asyncio.to_thread(lambda: list(query.stream()))
            deleted_count = 0
            for doc in docs:
                await asyncio.to_thread(doc.reference.delete)
                deleted_count += 1

            logger.debug(
                "Cache invalidated: user=%s, data_type=%s, count=%d",
                user_id,
                data_type,
                deleted_count,
            )

        except Exception as e:
            logger.warning("Cache invalidation error (non-critical): %s", str(e))
