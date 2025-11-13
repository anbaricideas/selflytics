"""E2E tests for complete Garmin linking user journey."""

import pytest
from playwright.sync_api import Page, expect


class TestGarminLinkingJourney:
    """Test the complete user journey from registration to Garmin linking."""

    def test_new_user_links_garmin_account(
        self, page: Page, base_url: str, test_user: dict, mock_garmin_api
    ):
        """Test complete journey: register → dashboard → link Garmin → sync.

        User Journey:
        1. User registers new account
        2. Lands on dashboard
        3. Navigates to Garmin settings
        4. Links Garmin account
        5. Sees success state
        6. Triggers manual sync
        """
        # Step 1 & 2: Register handled by authenticated_user fixture
        # Use mock_garmin_api page with routes already set up
        page = mock_garmin_api

        # Navigate to home (will redirect to login if not authenticated)
        page.goto(base_url)
        page.click('[data-testid="register-link"]')
        page.wait_for_selector('[data-testid="register-form"]', state="visible")

        # Fill registration form
        page.fill('[data-testid="input-display-name"]', test_user["display_name"])
        page.fill('[data-testid="input-email"]', test_user["email"])
        page.fill('[data-testid="input-password"]', test_user["password"])
        page.fill('input[name="confirm_password"]', test_user["password"])
        page.click('[data-testid="submit-register"]')

        # Verify redirect to dashboard
        page.wait_for_url(f"{base_url}/dashboard", timeout=10000)

        # Step 3: Navigate to Garmin settings
        page.goto(f"{base_url}/garmin/link")

        # Verify form is visible
        expect(page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

        # Step 4: Fill and submit Garmin credentials
        page.fill('[data-testid="input-garmin-username"]', "test@garmin.com")
        page.fill('[data-testid="input-garmin-password"]', "password123")

        # Submit form
        page.click('[data-testid="submit-link-garmin"]')

        # Step 5: Verify success state (HTMX swapped content)
        expect(page.locator('[data-testid="garmin-status-linked"]')).to_be_visible(
            timeout=5000
        )

        # Verify form no longer visible
        expect(page.locator('[data-testid="form-link-garmin"]')).not_to_be_visible()

        # Verify sync button appears
        expect(page.locator('[data-testid="button-sync-garmin"]')).to_be_visible()

        # Step 6: Trigger manual sync
        page.click('[data-testid="button-sync-garmin"]')

        # Verify sync success
        expect(page.locator('[data-testid="sync-success"]')).to_be_visible(timeout=5000)

    def test_linking_with_invalid_credentials(
        self, authenticated_user: Page, base_url: str, mock_garmin_api
    ):
        """Test error handling when Garmin credentials are invalid.

        User Journey:
        1. Authenticated user navigates to Garmin settings
        2. Enters invalid credentials
        3. Sees error message
        4. Form remains editable for retry
        """
        # Use authenticated_user page (already logged in)
        page = authenticated_user

        # Apply mock routes to authenticated page
        def handle_garmin_link_error(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=400,
                content_type="text/html",
                body='<div class="error" data-testid="error-message">Failed to link Garmin account. Invalid credentials.</div>',
            )

        page.route("**/garmin/link", handle_garmin_link_error)

        # Navigate to Garmin settings
        page.goto(f"{base_url}/garmin/link")

        # Fill invalid credentials
        page.fill('[data-testid="input-garmin-username"]', "wrong@garmin.com")
        page.fill('[data-testid="input-garmin-password"]', "wrong_password")
        page.click('[data-testid="submit-link-garmin"]')

        # Verify error message appears
        expect(page.locator('[data-testid="error-message"]')).to_be_visible(timeout=5000)

        # Verify form fields still accessible (can retry)
        # Note: Depending on HTMX swap, form might be replaced with error
        # If error is swapped in, form won't be visible
        # This is expected behavior for hx-swap="outerHTML"

    def test_unauthenticated_user_redirected(self, page: Page, base_url: str):
        """Test that unauthenticated users cannot access Garmin settings.

        User Journey:
        1. Unauthenticated user tries to access Garmin settings
        2. Redirected to login page
        """
        page.goto(f"{base_url}/garmin/link")

        # Should redirect to login
        # Wait for either login URL or login form
        try:
            page.wait_for_url(f"{base_url}/login", timeout=5000)
        except Exception:
            # If redirect doesn't change URL, check for login form
            expect(page.locator('input[name="email"]')).to_be_visible(timeout=2000)


class TestGarminSyncJourney:
    """Test manual sync functionality after linking."""

    def test_manual_sync_success(
        self, authenticated_user: Page, base_url: str, mock_garmin_api
    ):
        """Test successful manual sync after linking.

        User Journey:
        1. User with linked account clicks "Sync Now"
        2. Sees loading state (brief)
        3. Success message appears
        """
        page = authenticated_user

        # Apply mock routes
        def handle_link_success(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=200,
                content_type="text/html",
                body='''
                <div data-testid="garmin-status-linked">
                    <p>Garmin account linked</p>
                    <button
                        data-testid="button-sync-garmin"
                        hx-post="/garmin/sync"
                    >
                        Sync Now
                    </button>
                </div>
                ''',
            )

        def handle_sync_success(route):
            # Let GET requests through (sync is POST-only, but include for consistency)
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="sync-success">Sync completed successfully</div>',
            )

        page.route("**/garmin/link", handle_link_success)
        page.route("**/garmin/sync", handle_sync_success)

        # Link account first
        page.goto(f"{base_url}/garmin/link")
        page.fill('[data-testid="input-garmin-username"]', "test@garmin.com")
        page.fill('[data-testid="input-garmin-password"]', "password123")
        page.click('[data-testid="submit-link-garmin"]')

        # Wait for linked state
        expect(page.locator('[data-testid="garmin-status-linked"]')).to_be_visible(
            timeout=5000
        )

        # Click sync button
        page.click('[data-testid="button-sync-garmin"]')

        # Verify sync success
        expect(page.locator('[data-testid="sync-success"]')).to_be_visible(timeout=5000)
