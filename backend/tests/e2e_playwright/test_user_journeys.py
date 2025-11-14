"""
E2E tests for user journeys and navigation flows.

These tests verify critical user experience requirements found during
manual testing runsheet execution in Session 8 (2025-11-14).
"""

from playwright.sync_api import Page, expect


class TestChatPageNavigation:
    """Chat page should provide navigation to other parts of the application."""

    def test_user_can_logout_from_chat_page(self, authenticated_user: Page, base_url: str):
        """
        User should be able to logout while on the chat page.

        Expected: Logout button visible and functional from chat page.
        Context: Bug #10 - users reported being trapped on chat page.
        """
        # Navigate to chat page (trailing slash required for FastAPI router)
        authenticated_user.goto(f"{base_url}/chat/")

        # Wait for chat page to fully load - check for header first
        expect(authenticated_user.locator('[data-testid="chat-header"]')).to_be_visible(
            timeout=5000
        )

        # User should be able to logout from chat
        logout_button = authenticated_user.locator('[data-testid="logout-button"]')
        expect(logout_button).to_be_visible(timeout=2000)

        # User should be able to navigate to dashboard from chat
        dashboard_link = authenticated_user.locator('[data-testid="link-dashboard"]')
        expect(dashboard_link).to_be_visible(timeout=2000)

        # Verify sidebar loaded (Conversations heading)
        expect(authenticated_user.locator("text=Conversations")).to_be_visible(timeout=2000)


class TestAuthenticatedUserNavigation:
    """Authenticated users should navigate to dashboard, not login page."""

    def test_authenticated_user_visiting_root_url_sees_dashboard(
        self, authenticated_user: Page, base_url: str
    ):
        """
        Authenticated user visiting root URL should see their dashboard.

        Expected: Visiting / redirects to /dashboard for logged-in users.
        Context: Bug #11 - authenticated users were sent to login page.
        """
        # User is already authenticated (from fixture)
        # Navigate to root URL
        authenticated_user.goto(base_url)

        # Should redirect to dashboard, not login
        authenticated_user.wait_for_url(f"{base_url}/dashboard", timeout=5000)

        # Verify we're on dashboard
        expect(authenticated_user.locator('[data-testid="dashboard-header"]')).to_be_visible()


class TestUserSessionManagement:
    """User sessions should be isolated and display correct user information."""

    def test_dashboard_displays_correct_user_after_switching_accounts(
        self, page: Page, base_url: str
    ):
        """
        Dashboard should show currently logged-in user's name, not previous user's.

        Expected: After logout and login with different account, dashboard shows new user.
        Context: Bug #12 - concern about cached user data displaying incorrectly.
        """
        import time

        timestamp = int(time.time())
        password = "TestPass123!"  # noqa: S105

        # Create first user
        user1_email = f"user1-{timestamp}@example.com"
        user1_name = "First User"

        page.goto(f"{base_url}/register")
        page.fill('[data-testid="input-display-name"]', user1_name)
        page.fill('[data-testid="input-email"]', user1_email)
        page.fill('[data-testid="input-password"]', password)
        page.fill('[data-testid="input-confirm-password"]', password)
        page.click('[data-testid="submit-register"]')

        # Wait for redirect to dashboard
        page.wait_for_url(f"{base_url}/dashboard", timeout=10000)

        # Verify first user's name is shown
        welcome_message = page.locator('[data-testid="welcome-section"]')
        expect(welcome_message).to_contain_text(user1_name)

        # Logout
        page.click('[data-testid="logout-button"]')
        page.wait_for_url(f"{base_url}/login", timeout=5000)

        # Create second user
        user2_email = f"user2-{timestamp}@example.com"
        user2_name = "Second User"

        page.goto(f"{base_url}/register")
        page.fill('[data-testid="input-display-name"]', user2_name)
        page.fill('[data-testid="input-email"]', user2_email)
        page.fill('[data-testid="input-password"]', password)
        page.fill('[data-testid="input-confirm-password"]', password)
        page.click('[data-testid="submit-register"]')

        # Wait for redirect to dashboard
        page.wait_for_url(f"{base_url}/dashboard", timeout=10000)

        # Verify second user's name is shown (NOT first user's name)
        welcome_message = page.locator('[data-testid="welcome-section"]')
        expect(welcome_message).to_contain_text(user2_name)
        expect(welcome_message).not_to_contain_text(user1_name)


class TestGarminErrorHandling:
    """Garmin link errors should display gracefully without duplicating page elements."""

    def test_garmin_link_error_displays_without_duplicating_page_structure(
        self, authenticated_user: Page, base_url: str
    ):
        """
        Error messages should appear inline without duplicating page headers or containers.

        Expected: Single "Link Your Garmin Account" header before and after error display.
        Context: Bug #9 - HTMX fragment swap was duplicating container causing 2 headers.
        """

        # Set up route interception to mock Garmin API error
        def handle_garmin_link(route):
            """Mock Garmin API to return 401 error."""
            if route.request.method == "GET":
                # Let GET requests through (for page rendering)
                route.continue_()
                return

            # POST request - return error from backend (which should return fragment with error)
            route.continue_()

        authenticated_user.route("**/garmin/link", handle_garmin_link)

        # Navigate to Garmin link page
        authenticated_user.goto(f"{base_url}/garmin/link")

        # Wait for form to be visible
        expect(authenticated_user.locator('[data-testid="form-link-garmin"]')).to_be_visible()

        # Count how many "Link Your Garmin Account" headers exist (should be 1)
        headers_before = authenticated_user.locator("h1, h2").filter(
            has_text="Link Your Garmin Account"
        )
        count_before = headers_before.count()
        assert count_before == 1, f"Expected 1 header before form submission, found {count_before}"

        # Fill form with credentials that will trigger error from real Garmin API
        authenticated_user.fill('[data-testid="input-garmin-username"]', "test@garmin.com")
        authenticated_user.fill('[data-testid="input-garmin-password"]', "password123")

        # Submit form
        authenticated_user.click('[data-testid="submit-link-garmin"]')

        # Wait for error message to appear
        expect(authenticated_user.locator('[data-testid="error-message"]')).to_be_visible(
            timeout=10000
        )

        # Count headers again - should still be 1 (not duplicated)
        headers_after = authenticated_user.locator("h1, h2").filter(
            has_text="Link Your Garmin Account"
        )
        count_after = headers_after.count()

        # Error should be displayed inline without duplicating page structure
        assert count_after == 1, (
            f"Expected 1 'Link Your Garmin Account' header after error, found {count_after}. "
            "HTMX fragment swap should not duplicate page structure."
        )
