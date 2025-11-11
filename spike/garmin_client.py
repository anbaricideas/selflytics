"""Garmin Connect client (adapted from garmin_agents for spike validation)."""

import json
from datetime import date
from pathlib import Path
from typing import Any

import garth


class GarminClient:
    """Simplified async-compatible wrapper around garth library for spike testing."""

    def __init__(self, cache_dir: str = "spike/cache"):
        """Initialize Garmin client with local file caching."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.cache_dir / "garmin_tokens"
        self.authenticated = False
        # Use instance-level garth client (not module-level state)
        self.garth_client = garth.Client()

    async def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with Garmin Connect (supports MFA).

        For spike: Tries to load existing tokens first, then fresh login if needed.
        MFA requires manual input via console (simplified flow for spike).

        Args:
            username: Garmin Connect email
            password: Garmin Connect password

        Returns:
            True if authentication successful, False otherwise
        """
        # Try to resume existing session first
        if await self.load_tokens():
            # Validate tokens with quick API test
            if await self._test_connection():
                print("✓ Resumed session from cached tokens")
                self.authenticated = True
                return True

        # Fresh login required
        try:
            print(f"Authenticating with Garmin Connect as {username}...")

            # login() returns either:
            # - True (success)
            # - ("needs_mfa", mfa_data) (MFA required)
            result = self.garth_client.login(username, password, return_on_mfa=True)

            if result is True:
                # Success - no MFA
                print("✓ Authentication successful")
                self.authenticated = True
                await self._save_tokens()
                return True
            elif isinstance(result, tuple) and result[0] == "needs_mfa":
                # MFA required - for spike, use interactive prompt
                print("\n⚠️  MFA code required")
                mfa_code = input("Enter MFA code from your authenticator app: ").strip()

                # Complete MFA login
                mfa_data = result[1]
                self.garth_client.resume_login(mfa_data, mfa_code)

                print("✓ MFA authentication successful")
                self.authenticated = True
                await self._save_tokens()
                return True
            else:
                print(f"✗ Unexpected login result: {result}")
                return False

        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False

    async def load_tokens(self) -> bool:
        """Load saved tokens from cache directory."""
        if not self.token_file.exists():
            return False

        try:
            # garth uses .dump()/.load() for token persistence
            self.garth_client.load(str(self.token_file))
            return True
        except Exception as e:
            print(f"Token load failed: {e}")
            return False

    async def _save_tokens(self) -> None:
        """Save current tokens to cache directory."""
        try:
            self.garth_client.dump(str(self.token_file))
        except Exception as e:
            print(f"Token save failed: {e}")

    async def _test_connection(self) -> bool:
        """Test if current tokens are valid with a simple API call."""
        try:
            # Try fetching user summary (lightweight endpoint)
            garth.connectapi(
                "/usersummary-service/usersummary/daily/today", client=self.garth_client
            )
            return True
        except Exception:
            return False

    async def get_activities(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """
        Fetch activities in date range.

        For spike: Simplified implementation that fetches all activities
        and filters by date client-side (production would use date parameters).

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of activity dictionaries
        """
        if not self.authenticated:
            raise Exception("Not authenticated - call authenticate() first")

        # Calculate how many days of activities to fetch
        days = (end_date - start_date).days + 1
        limit = min(days * 3, 100)  # Estimate ~3 activities per day, cap at 100

        try:
            # Fetch activities from Garmin Connect API
            endpoint = f"/activitylist-service/activities?start=0&limit={limit}"
            response = garth.connectapi(endpoint, client=self.garth_client)

            # Extract activity list from response
            if not response or "activityList" not in response:
                print("⚠️  No activities found in response")
                return []

            all_activities = response["activityList"]

            # Filter by date range (client-side filtering for spike)
            filtered_activities = []
            for activity in all_activities:
                # Parse activity start time
                activity_date_str = activity.get("startTimeLocal", "")
                if not activity_date_str:
                    continue

                # Extract date (format: "2025-11-09 14:30:00")
                activity_date = date.fromisoformat(activity_date_str.split()[0])

                # Check if within range
                if start_date <= activity_date <= end_date:
                    filtered_activities.append(activity)

            # Cache results
            cache_file = self.cache_dir / f"activities_{start_date}_{end_date}.json"
            cache_file.write_text(
                json.dumps(filtered_activities, indent=2, default=str)
            )

            print(
                f"✓ Fetched {len(filtered_activities)} activities from {start_date} to {end_date}"
            )
            return filtered_activities

        except Exception as e:
            print(f"✗ Failed to fetch activities: {e}")
            return []

    async def get_daily_metrics(self, target_date: date) -> dict[str, Any]:
        """
        Fetch daily metrics for specific date.

        For spike: Returns summary data including steps, heart rate, sleep.

        Args:
            target_date: Date to fetch metrics for

        Returns:
            Dictionary of daily metrics
        """
        if not self.authenticated:
            raise Exception("Not authenticated")

        try:
            # For "today", use special endpoint
            if target_date == date.today():
                endpoint = "/usersummary-service/usersummary/daily/today"
            else:
                # For historical dates, use date-specific endpoint
                date_str = target_date.isoformat()
                endpoint = f"/usersummary-service/usersummary/daily/{date_str}"

            metrics = garth.connectapi(endpoint, client=self.garth_client)

            # Cache results
            cache_file = self.cache_dir / f"metrics_{target_date}.json"
            cache_file.write_text(json.dumps(metrics, indent=2, default=str))

            return metrics

        except Exception as e:
            print(f"✗ Failed to fetch metrics for {target_date}: {e}")
            return {}
