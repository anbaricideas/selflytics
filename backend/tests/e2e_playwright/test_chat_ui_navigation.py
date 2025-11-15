"""E2E tests for chat UI navigation and banner interactions.

Tests the Garmin connection banner dismissal flow and navigation.
"""

import time

from playwright.async_api import Page, expect


class TestGarminBanner:
    """Tests for Garmin connection banner on chat page."""

    async def test_user_can_dismiss_banner_and_it_stays_hidden(
        self, authenticated_user: Page, base_url: str
    ):
        """User can dismiss banner and it stays hidden on refresh."""
        # Navigate to chat (authenticated_user fixture lands on /dashboard from Phase 0)
        # Phase 1 redirects root to /chat, but existing tests still use /dashboard
        await authenticated_user.goto(f"{base_url}/chat/")

        # Banner should be visible initially (test user has no Garmin linked)
        banner = authenticated_user.locator('[data-testid="garmin-banner"]')
        await expect(banner).to_be_visible(timeout=5000)

        # Dismiss banner
        dismiss_btn = authenticated_user.locator('[data-testid="banner-dismiss"]')
        await dismiss_btn.click()

        # Banner should be hidden
        await expect(banner).to_be_hidden()

        # Refresh page
        await authenticated_user.reload()

        # Banner should still be hidden (localStorage persisted)
        await expect(banner).to_be_hidden(timeout=5000)

    async def test_banner_reappears_after_logout_and_login(self, page: Page, base_url: str):
        """Banner reappears after user logs out and logs back in."""
        timestamp = int(time.time())
        email = f"banner-test-{timestamp}@example.com"
        password = "TestPass123!"  # noqa: S105 - test fixture, not a real credential

        # Register new user
        await page.goto(f"{base_url}/register")
        await page.fill('[data-testid="input-display-name"]', "Banner Test")
        await page.fill('[data-testid="input-email"]', email)
        await page.fill('[data-testid="input-password"]', password)
        await page.fill('[data-testid="input-confirm-password"]', password)
        await page.click('[data-testid="submit-register"]')

        # Phase 1 routing: registration should redirect to /chat (not /dashboard)
        # However, HTMX registration might still redirect to /dashboard
        # Let's check for either and navigate to chat if needed
        try:
            await page.wait_for_url(f"{base_url}/chat/", timeout=5000)
        except Exception:
            # If not at /chat, might be at /dashboard - navigate to chat
            await page.goto(f"{base_url}/chat/")

        # Banner should be visible
        banner = page.locator('[data-testid="garmin-banner"]')
        await expect(banner).to_be_visible(timeout=5000)

        # Dismiss banner
        await page.click('[data-testid="banner-dismiss"]')
        await expect(banner).to_be_hidden()

        # Logout
        await page.click('[data-testid="logout-button"]')
        await page.wait_for_url(f"{base_url}/login", timeout=5000)

        # Login again
        await page.fill('input[name="username"]', email)
        await page.fill('input[name="password"]', password)
        await page.click('[data-testid="submit-login"]')

        # Phase 1 routing: login should redirect to /chat (not /dashboard)
        # Check where we landed and navigate to chat if needed
        try:
            await page.wait_for_url(f"{base_url}/chat/", timeout=5000)
        except Exception:
            # If not at /chat, navigate there
            await page.goto(f"{base_url}/chat/")

        # Banner should be visible again (localStorage cleared on logout)
        await expect(banner).to_be_visible(timeout=5000)

    async def test_banner_link_navigates_to_garmin_oauth(
        self, authenticated_user: Page, base_url: str
    ):
        """Clicking Link Now button navigates to Garmin OAuth page."""
        # Navigate to chat
        await authenticated_user.goto(f"{base_url}/chat/")

        # Wait for banner to be visible
        banner = authenticated_user.locator('[data-testid="garmin-banner"]')
        await expect(banner).to_be_visible(timeout=5000)

        # Click "Link Now" button
        link_button = authenticated_user.locator('[data-testid="banner-link-now"]')
        await link_button.click()

        # Should navigate to /garmin/link
        await authenticated_user.wait_for_url(f"{base_url}/garmin/link", timeout=5000)

        # Verify we're on the Garmin link page (check for email input)
        await expect(authenticated_user.locator('input[name="garmin_email"]')).to_be_visible(
            timeout=3000
        )
