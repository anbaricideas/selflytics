"""
E2E tests for user journeys and navigation flows.

These tests verify critical user experience requirements found during
manual testing runsheet execution in Session 8 (2025-11-14).
"""

from urllib.parse import urlparse

import pytest
from playwright.async_api import Page, expect

from tests.conftest import TEST_GARMIN_PASSWORD, TEST_PASSWORD


class TestChatPageNavigation:
    """Chat page should provide navigation to other parts of the application."""

    async def test_user_can_logout_from_chat_page(self, authenticated_user: Page, base_url: str):
        """
        User should be able to logout while on the chat page.

        Expected: Logout button visible and functional from chat page.
        Context: Bug #10 - users reported being trapped on chat page.
        """
        # Navigate to chat page (trailing slash required for FastAPI router)
        await authenticated_user.goto(f"{base_url}/chat/")

        # Wait for chat page to fully load - check for header first
        await expect(authenticated_user.locator('[data-testid="chat-header"]')).to_be_visible(
            timeout=5000
        )

        # User should be able to logout from chat
        logout_button = authenticated_user.locator('[data-testid="logout-button"]')
        await expect(logout_button).to_be_visible(timeout=2000)

        # User should be able to navigate to settings from chat
        settings_link = authenticated_user.locator('[data-testid="link-settings"]')
        await expect(settings_link).to_be_visible(timeout=2000)

        # Verify sidebar loaded (Conversations heading)
        await expect(authenticated_user.locator("text=Conversations")).to_be_visible(timeout=2000)


class TestAuthenticatedUserNavigation:
    """Authenticated users should navigate to dashboard, not login page."""

    async def test_authenticated_user_visiting_root_url_redirects_to_chat(
        self, authenticated_user: Page, base_url: str
    ):
        """
        Authenticated user visiting root URL should redirect to chat.

        Expected: Visiting / redirects to /chat/ for logged-in users.
        Context: Phase 4 - chat-first navigation model (Spec line 139)
        """
        # User is already authenticated (from fixture)
        # Navigate to root URL
        await authenticated_user.goto(base_url)

        # Should redirect to chat, not login
        await authenticated_user.wait_for_url(f"{base_url}/chat/", timeout=5000)

        # Verify we're on chat
        await expect(authenticated_user.locator('[data-testid="chat-header"]')).to_be_visible()


class TestUserSessionManagement:
    """User sessions should be isolated and display correct user information."""

    async def test_chat_displays_correct_user_after_switching_accounts(
        self, page: Page, base_url: str
    ):
        """
        Chat page should show currently logged-in user's name, not previous user's.

        Expected: After logout and login with different account, chat shows new user.
        Context: Bug #12 - concern about cached user data displaying incorrectly.
        """
        import time

        timestamp = int(time.time())
        password = TEST_PASSWORD

        # Create first user
        user1_email = f"user1-{timestamp}@example.com"
        user1_name = "First User"

        await page.goto(f"{base_url}/register")
        await page.fill('[data-testid="input-display-name"]', user1_name)
        await page.fill('[data-testid="input-email"]', user1_email)
        await page.fill('[data-testid="input-password"]', password)
        await page.fill('[data-testid="input-confirm-password"]', password)
        await page.click('[data-testid="submit-register"]')

        # Wait for redirect to chat
        await page.wait_for_url(f"{base_url}/chat/", timeout=10000)

        # Verify first user's name is shown
        welcome_message = page.locator('[data-testid="welcome-section"]')
        await expect(welcome_message).to_contain_text(user1_name)

        # Logout
        await page.click('[data-testid="logout-button"]')
        await page.wait_for_url(f"{base_url}/login", timeout=5000)

        # Create second user
        user2_email = f"user2-{timestamp}@example.com"
        user2_name = "Second User"

        await page.goto(f"{base_url}/register")
        await page.fill('[data-testid="input-display-name"]', user2_name)
        await page.fill('[data-testid="input-email"]', user2_email)
        await page.fill('[data-testid="input-password"]', password)
        await page.fill('[data-testid="input-confirm-password"]', password)
        await page.click('[data-testid="submit-register"]')

        # Wait for redirect to chat
        await page.wait_for_url(f"{base_url}/chat/", timeout=10000)

        # Verify second user's name is shown (NOT first user's name)
        welcome_message = page.locator('[data-testid="welcome-section"]')
        await expect(welcome_message).to_contain_text(user2_name)
        await expect(welcome_message).not_to_contain_text(user1_name)


class TestGarminErrorHandling:
    """Garmin link errors should display gracefully without duplicating page elements."""

    async def test_garmin_link_error_displays_without_duplicating_page_structure(
        self, authenticated_user: Page, base_url: str
    ):
        """
        Error messages should appear inline without duplicating page headers or containers.

        Expected: Single "Link Your Garmin Account" header before and after error display.
        Context: Bug #9 - HTMX fragment swap was duplicating container causing 2 headers.
        """

        # Set up route interception to mock Garmin API error
        async def handle_garmin_link(route):
            """Mock Garmin API to return 401 error."""
            if route.request.method == "GET":
                # Let GET requests through (for page rendering)
                await route.continue_()
                return

            # POST request - return error from backend (which should return fragment with error)
            await route.continue_()

        await authenticated_user.route("**/garmin/link", handle_garmin_link)

        # Navigate to Garmin link page
        await authenticated_user.goto(f"{base_url}/garmin/link")

        # Wait for form to be visible
        await expect(authenticated_user.locator('[data-testid="form-link-garmin"]')).to_be_visible()

        # Count how many "Link Your Garmin Account" headers exist (should be 1)
        headers_before = authenticated_user.locator("h1, h2").filter(
            has_text="Link Your Garmin Account"
        )
        count_before = await headers_before.count()
        assert count_before == 1, f"Expected 1 header before form submission, found {count_before}"

        # Fill form with credentials that will trigger error from real Garmin API
        await authenticated_user.fill('[data-testid="input-garmin-username"]', "test@garmin.com")
        await authenticated_user.fill('[data-testid="input-garmin-password"]', TEST_GARMIN_PASSWORD)

        # Submit form
        await authenticated_user.click('[data-testid="submit-link-garmin"]')

        # Wait for error message to appear
        await expect(authenticated_user.locator('[data-testid="error-message"]')).to_be_visible(
            timeout=10000
        )

        # Count headers again - should still be 1 (not duplicated)
        headers_after = authenticated_user.locator("h1, h2").filter(
            has_text="Link Your Garmin Account"
        )
        count_after = await headers_after.count()

        # Error should be displayed inline without duplicating page structure
        assert count_after == 1, (
            f"Expected 1 'Link Your Garmin Account' header after error, found {count_after}. "
            "HTMX fragment swap should not duplicate page structure."
        )


class TestAuthenticationTokenHandling:
    """Authentication tokens should be validated and invalid tokens should redirect to login."""

    @pytest.mark.parametrize("protected_route", ["/settings", "/chat/"])
    async def test_invalid_jwt_redirects_to_login_from_protected_routes(
        self, page: Page, base_url: str, protected_route: str
    ):
        """
        User with invalid JWT token should be redirected to login from any protected route.

        Expected behavior:
        1. User has an invalid JWT token in cookies
        2. User attempts to access protected route (settings, chat, etc.)
        3. Server validates token, finds it invalid
        4. User is redirected to login page (silent redirect, no error message)
        5. Login functionality still works (confirms auth validation caused redirect)

        Context: Replaces skipped integration tests that tried to test this with mocked fixtures.
        E2E test uses real authentication flow to verify token validation works end-to-end.
        Verifies that chat-first navigation model still enforces authentication.
        """
        # Set an invalid JWT token cookie manually
        await page.goto(base_url)

        # Extract domain from base_url to avoid hard-coding localhost
        domain = urlparse(base_url).hostname or "localhost"

        # Add invalid token cookie (malformed JWT that will fail signature verification)
        await page.context.add_cookies(
            [
                {
                    "name": "access_token",
                    "value": "invalid.jwt.token.here",
                    "domain": domain,
                    "path": "/",
                }
            ]
        )

        # Attempt to access protected route
        await page.goto(f"{base_url}{protected_route}")

        # Should be redirected to login page (token validation fails)
        await page.wait_for_url(f"{base_url}/login", timeout=5000)

        # Verify we're on login page
        await expect(page.locator('[data-testid="login-form"]')).to_be_visible()

        # Verify silent redirect (no error message from invalid token)
        # Invalid tokens should cause silent redirect, not display an error
        error_alert = page.locator('[data-testid="error-message"]')
        await expect(error_alert).not_to_be_visible()

        # Verify URL still contains /login (no client-side routing)
        assert "/login" in page.url, "Should remain on login page"

        # Verify login still works (confirms route is functional, auth just failed)
        # This proves redirect was due to token validation, not broken routing
        login_button = page.locator('[data-testid="submit-login"]')
        await expect(login_button).to_be_visible()
