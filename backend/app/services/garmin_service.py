"""Garmin service for OAuth and data management."""

import logging
from datetime import date, timedelta
from typing import Any

from app.services.garmin_client import GarminClient
from app.services.garth_wrapper import get_user_profile_typed
from app.services.user_service import UserService
from app.utils.cache import GarminDataCache


logger = logging.getLogger(__name__)


class GarminService:
    """High-level Garmin integration service."""

    def __init__(self, user_id: str):
        """
        Initialize GarminService for a specific user.

        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.client = GarminClient(user_id)
        self.cache = GarminDataCache()
        self.user_service = UserService()

    async def link_account(self, username: str, password: str) -> bool:
        """
        Link Garmin account to user.

        Args:
            username: Garmin account username/email
            password: Garmin account password

        Returns:
            True if successful, False otherwise
        """
        # Authenticate
        success = await self.client.authenticate(username, password)

        if success:
            # Update user record
            await self.user_service.update_garmin_status(user_id=self.user_id, linked=True)

            # Initial data sync
            await self.sync_recent_data()

            logger.info("Garmin account linked for user %s", self.user_id)

        return success

    async def unlink_account(self) -> bool:
        """
        Unlink Garmin account by deleting tokens and cache.

        Returns:
            True if successful

        Raises:
            Exception: If deletion fails
        """
        # Delete tokens from Firestore
        await self.client.delete_tokens()

        # Invalidate all cached data for user
        await self.cache.invalidate(self.user_id)

        # Update user record
        await self.user_service.update_garmin_status(user_id=self.user_id, linked=False)

        logger.info("Garmin account unlinked for user %s", self.user_id)
        return True

    async def sync_recent_data(self) -> None:
        """Sync last 30 days of activities and metrics."""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        # Fetch activities
        activities = await self.client.get_activities(start_date, end_date)

        # Cache activities
        date_range = f"{start_date}:{end_date}"
        await self.cache.set(
            user_id=self.user_id,
            data_type="activities",
            data=[activity.model_dump() for activity in activities],
            date_range=date_range,
        )

        logger.info("Synced %d activities for user %s", len(activities), self.user_id)

    async def get_activities_cached(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """
        Get activities with caching.

        Args:
            start_date: Start date for activity range
            end_date: End date for activity range

        Returns:
            List of activity dictionaries
        """
        date_range = f"{start_date}:{end_date}"

        # Check cache
        try:
            cached = await self.cache.get(
                user_id=self.user_id, data_type="activities", date_range=date_range
            )

            if cached:
                logger.debug("Cache hit for activities %s", date_range)
                result_list: list[dict[str, Any]] = cached
                return result_list
        except Exception as e:
            logger.warning("Cache get error, falling back to API: %s", str(e))

        # Fetch from API
        activities = await self.client.get_activities(start_date, end_date)

        # Cache results
        try:
            await self.cache.set(
                user_id=self.user_id,
                data_type="activities",
                data=[activity.model_dump() for activity in activities],
                date_range=date_range,
            )
        except Exception as e:
            logger.warning("Cache set error (non-critical): %s", str(e))

        return [activity.model_dump() for activity in activities]

    async def get_daily_metrics_cached(self, target_date: date) -> dict[str, Any]:
        """
        Get daily metrics with caching.

        Args:
            target_date: Date for which to fetch metrics

        Returns:
            Dict with daily metrics (steps, resting_heart_rate, sleep_seconds, avg_stress_level)
        """
        date_range = str(target_date)

        # Check cache
        try:
            cached = await self.cache.get(
                user_id=self.user_id, data_type="daily_metrics", date_range=date_range
            )

            if cached:
                logger.debug("Cache hit for daily metrics %s", date_range)
                result_dict: dict[str, Any] = cached
                return result_dict
        except Exception as e:
            logger.warning("Cache get error, falling back to API: %s", str(e))

        # Fetch from API
        metrics = await self.client.get_daily_metrics(target_date)

        # Convert to dict for caching
        metrics_dict = metrics.model_dump()

        # Cache results
        try:
            await self.cache.set(
                user_id=self.user_id,
                data_type="daily_metrics",
                data=metrics_dict,
                date_range=date_range,
            )
        except Exception as e:
            logger.warning("Cache set error (non-critical): %s", str(e))

        return metrics_dict

    async def get_user_profile(self) -> dict[str, Any]:
        """
        Get user profile information from Garmin.

        Returns:
            Dictionary with user profile data including display_name

        Note:
            Returns "User" as default display_name if not available in garth.client.profile
        """
        # Load tokens to ensure garth is authenticated
        await self.client.load_tokens()

        # Access garth.client.profile for display name
        profile = get_user_profile_typed()
        display_name: str = profile.get("displayName", "User")

        return {"display_name": display_name}
