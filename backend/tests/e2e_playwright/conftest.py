"""Shared fixtures for Playwright E2E tests."""

import os
import time
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def base_url():
    """Get base URL from environment or use local default.

    Priority:
    1. TEST_BASE_URL (for deployed environments)
    2. BASE_URL from .env (for local testing)
    3. Default localhost:8000
    """
    test_url = os.getenv("TEST_BASE_URL")
    if test_url:
        return test_url.rstrip("/")

    # Load from .env for local testing
    backend_dir = Path(__file__).parent.parent.parent
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    return os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


@pytest.fixture
def test_user():
    """Generate unique test user credentials."""
    timestamp = int(time.time())
    test_id = uuid.uuid4().hex[:6]
    return {
        "email": f"e2e-garmin-{test_id}-{timestamp}@example.com",
        "password": "TestPass123!",  # noqa: S105
        "display_name": f"E2E Test User {test_id}",
    }


@pytest.fixture
def authenticated_user(page: Page, base_url: str, test_user: dict):
    """Register and login a test user.

    Returns:
        Page object with authenticated session
    """
    # Navigate to registration
    page.goto(base_url)
    page.click("text=Register")
    page.wait_for_selector('input[name="email"]', state="visible")

    # Fill registration form
    page.fill('input[name="display_name"]', test_user["display_name"])
    page.fill('input[name="email"]', test_user["email"])
    page.fill('input[name="password"]', test_user["password"])
    page.click('button[type="submit"]')

    # Wait for dashboard redirect
    page.wait_for_url(f"{base_url}/dashboard", timeout=10000)

    return page


@pytest.fixture
def user_with_garmin_unlinked(authenticated_user: Page):
    """Authenticated user without Garmin linked.

    Returns:
        Page object with auth session, ready to link Garmin
    """
    return authenticated_user


@pytest.fixture
def mock_garmin_api(page: Page):
    """Mock Garmin API responses for testing without real credentials.

    This uses Playwright's route interception to mock HTTP responses.
    """
    def handle_garmin_login(route):
        """Mock successful Garmin authentication."""
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"status": "success", "oauth1_token": "mock_token", "oauth2_token": "mock_token"}'
        )

    def handle_garmin_activities(route):
        """Mock Garmin activities response."""
        route.fulfill(
            status=200,
            content_type="application/json",
            body='''[
                {
                    "activityId": 12345,
                    "activityName": "Morning Run",
                    "activityType": "running",
                    "startTimeLocal": "2025-01-13T06:30:00",
                    "distance": 5000,
                    "duration": 1800,
                    "averageHR": 145,
                    "calories": 350
                }
            ]'''
        )

    # Intercept Garmin Connect API calls
    page.route("**/connect.garmin.com/**", handle_garmin_login)
    page.route("**/garmin/activities**", handle_garmin_activities)

    return page
