"""Garmin Connect client (async wrapper around garth)."""

import logging
from datetime import date, datetime, timedelta

import garth

from app.db.firestore_client import get_firestore_client
from app.models.garmin_data import DailyMetrics, GarminActivity, HealthSnapshot
from app.models.garmin_token import GarminToken
from app.utils.encryption import decrypt_token, encrypt_token


logger = logging.getLogger(__name__)


class GarminClient:
    """Async Garmin Connect client with token encryption and Firestore storage."""

    def __init__(self, user_id: str):
        """Initialize GarminClient for a specific user.

        Args:
            user_id: User ID for token storage and retrieval
        """
        self.user_id = user_id
        self.db = get_firestore_client()
        self.tokens_collection = self.db.collection("garmin_tokens")

    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with Garmin Connect (supports MFA).

        Args:
            username: Garmin email/username
            password: Garmin password

        Returns:
            True if authentication successful, False otherwise

        Note:
            MFA prompts are handled interactively by garth if required.
        """
        try:
            # garth login (may prompt for MFA in terminal)
            garth.login(username, password)

            # Save tokens after successful authentication
            await self._save_tokens()

            logger.info("Garmin authentication successful for user %s", self.user_id)
            return True

        except Exception as e:
            logger.error("Garmin authentication failed: %s", str(e))
            return False

    async def load_tokens(self) -> bool:
        """Load saved tokens from Firestore.

        Returns:
            True if tokens loaded successfully, False otherwise
        """
        try:
            doc = self.tokens_collection.document(self.user_id).get()
            if not doc.exists:
                logger.debug("No tokens found for user %s", self.user_id)
                return False

            token_data = GarminToken(**doc.to_dict())

            # Decrypt tokens
            oauth1 = decrypt_token(token_data.oauth1_token_encrypted)
            oauth2 = decrypt_token(token_data.oauth2_token_encrypted)

            # Set garth tokens
            garth.client.oauth1_token = oauth1
            garth.client.oauth2_token = oauth2

            logger.debug("Tokens loaded successfully for user %s", self.user_id)
            return True

        except Exception as e:
            logger.error("Failed to load tokens: %s", str(e))
            return False

    async def _save_tokens(self):
        """Save garth tokens to Firestore (encrypted).

        Raises:
            Exception: If token encryption or Firestore save fails
        """
        # Encrypt tokens
        oauth1_encrypted = encrypt_token(garth.client.oauth1_token)
        oauth2_encrypted = encrypt_token(garth.client.oauth2_token)

        # Create token document
        now = datetime.utcnow()
        token = GarminToken(
            user_id=self.user_id,
            oauth1_token_encrypted=oauth1_encrypted,
            oauth2_token_encrypted=oauth2_encrypted,
            token_expiry=None,  # garth handles expiry internally
            last_sync=now,
            mfa_enabled=False,  # Can detect from auth flow in future
            created_at=now,
            updated_at=now,
        )

        # Save to Firestore
        self.tokens_collection.document(self.user_id).set(token.model_dump())
        logger.debug("Tokens saved successfully for user %s", self.user_id)

    async def get_activities(
        self,
        start_date: date,
        end_date: date,
        activity_type: str | None = None,
    ) -> list[GarminActivity]:
        """Fetch activities in date range.

        Args:
            start_date: Start date for activity range
            end_date: End date for activity range (inclusive)
            activity_type: Optional activity type filter (e.g., "running", "cycling")

        Returns:
            List of GarminActivity objects

        Raises:
            Exception: If not authenticated (no tokens available)
        """
        # Ensure authenticated
        if not await self.load_tokens():
            raise Exception("Not authenticated - user must link Garmin account")

        activities = []
        current_date = start_date

        while current_date <= end_date:
            try:
                # garth API call
                day_activities = garth.activities(current_date.isoformat())

                # Parse and validate
                for activity_data in day_activities:
                    activity = GarminActivity(**activity_data)

                    # Filter by type if specified
                    if activity_type is None or activity.activity_type == activity_type:
                        activities.append(activity)

            except Exception as e:
                logger.warning(
                    "Failed to fetch activities for %s: %s",
                    current_date,
                    str(e),
                )

            current_date += timedelta(days=1)

        logger.debug(
            "Fetched %d activities for user %s (%s to %s)",
            len(activities),
            self.user_id,
            start_date,
            end_date,
        )
        return activities

    async def get_daily_metrics(self, target_date: date) -> DailyMetrics:
        """Fetch daily summary metrics.

        Args:
            target_date: Date for which to fetch metrics

        Returns:
            DailyMetrics object with steps, calories, heart rate, etc.

        Raises:
            Exception: If not authenticated
        """
        if not await self.load_tokens():
            raise Exception("Not authenticated - user must link Garmin account")

        # garth API call
        summary = garth.daily_summary(target_date.isoformat())

        # Parse to model
        return DailyMetrics(
            date=target_date,
            steps=summary.get("steps"),
            distance_meters=summary.get("distanceMeters"),
            active_calories=summary.get("activeCalories"),
            resting_heart_rate=summary.get("restingHeartRate"),
            max_heart_rate=summary.get("maxHeartRate"),
            avg_stress_level=summary.get("avgStressLevel"),
            sleep_seconds=summary.get("sleepSeconds"),
        )

    async def get_health_snapshot(self) -> HealthSnapshot:
        """Fetch latest health snapshot.

        Returns:
            HealthSnapshot object with current health metrics

        Raises:
            Exception: If not authenticated
        """
        if not await self.load_tokens():
            raise Exception("Not authenticated - user must link Garmin account")

        # garth API call for latest health data
        health_data = garth.health_snapshot()

        return HealthSnapshot(
            timestamp=datetime.utcnow(),
            heart_rate=health_data.get("heartRate"),
            respiration_rate=health_data.get("respirationRate"),
            stress_level=health_data.get("stressLevel"),
            spo2=health_data.get("spo2"),
        )
