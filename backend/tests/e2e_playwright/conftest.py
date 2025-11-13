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
    3. Construct from PORT variable in .env
    4. Default localhost:8000
    """
    test_url = os.getenv("TEST_BASE_URL")
    if test_url:
        return test_url.rstrip("/")

    # Load from .env.local (preferred) or .env for local testing
    backend_dir = Path(__file__).parent.parent.parent
    env_local_file = backend_dir / ".env.local"
    env_file = backend_dir / ".env"

    if env_local_file.exists():
        load_dotenv(env_local_file)
    elif env_file.exists():
        load_dotenv(env_file)

    # Check for explicit BASE_URL first
    base = os.getenv("BASE_URL")
    if base:
        return base.rstrip("/")

    # Otherwise construct from PORT
    port = os.getenv("PORT", "8000")
    return f"http://localhost:{port}"


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
        "password": "TestPass123!",
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
    page.click('[data-testid="register-link"]')
    page.wait_for_selector('[data-testid="register-form"]', state="visible")

    # Fill registration form with data-testid selectors
    page.fill('[data-testid="input-display-name"]', test_user["display_name"])
    page.fill('[data-testid="input-email"]', test_user["email"])
    page.fill('[data-testid="input-password"]', test_user["password"])
    page.fill('input[name="confirm_password"]', test_user["password"])
    page.click('[data-testid="submit-register"]')

    # Wait for HTMX redirect (HX-Redirect header triggers client-side navigation)
    # HTMX will receive the HX-Redirect header and navigate to /dashboard
    page.wait_for_url(f"{base_url}/dashboard", timeout=10000)

    return page

    # TODO: Cleanup - delete test user from Firestore
    # Requires Firestore admin client fixture
    # For now, unique emails prevent collision


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
    Returns HTML fragments for HTMX responses.
    """

    def handle_garmin_link(route):
        """Mock successful Garmin link endpoint.

        Only intercepts POST requests. GET requests are passed through to the
        real backend to render the form template.
        """
        request = route.request

        # Let GET requests through to real backend
        if request.method == "GET":
            route.continue_()
            return

        # Handle POST requests
        post_data = request.post_data

        # Simple mock: accept test@garmin.com, reject others
        # Note: post_data can be bytes or string depending on Playwright version
        # Check for both raw and URL-encoded email (@ becomes %40 in form data)
        has_test_email = (
            (isinstance(post_data, bytes) and (b"test@garmin.com" in post_data or b"test%40garmin.com" in post_data))
            or (isinstance(post_data, str) and ("test@garmin.com" in post_data or "test%40garmin.com" in post_data))
        )
        if post_data and has_test_email:
            # Return HTML fragment for HTMX swap (outerHTML)
            route.fulfill(
                status=200,
                content_type="text/html",
                body="""
                <div data-testid="garmin-status-linked" class="bg-green-50 border border-green-200 rounded-lg p-6">
                    <p class="text-green-800 font-semibold">Garmin account linked</p>
                    <button
                        data-testid="button-sync-garmin"
                        hx-post="/garmin/sync"
                        hx-swap="outerHTML"
                        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md"
                    >
                        Sync Now
                    </button>
                </div>
                """,
            )
        else:
            # Invalid credentials
            route.fulfill(
                status=400,
                content_type="text/html",
                body='<div class="error" data-testid="error-message">Failed to link Garmin account. Invalid credentials.</div>',
            )

    def handle_garmin_sync(route):
        """Mock successful Garmin sync endpoint."""
        # Simulate brief delay
        route.fulfill(
            status=200,
            content_type="text/html",
            body="""
            <div data-testid="sync-success" class="text-green-600">
                Sync completed successfully
            </div>
            """,
        )

    # Intercept backend Garmin endpoints
    page.route("**/garmin/link", handle_garmin_link)
    page.route("**/garmin/sync", handle_garmin_sync)

    return page
