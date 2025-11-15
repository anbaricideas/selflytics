"""
E2E tests for settings page navigation and user flows.

Tests verify settings page accessibility, logout functionality,
and navigation between chat and settings pages.
"""

from playwright.async_api import Page, expect


class TestLogoutFlow:
    """Users should be able to logout from the settings page."""

    async def test_user_can_logout_from_settings_page(
        self, authenticated_user: Page, base_url: str
    ):
        """
        Verify complete logout flow from settings page.

        Expected behavior:
        1. User navigates to settings page
        2. User clicks logout button
        3. User is redirected to login page
        4. User session is cleared
        """
        # Navigate to settings page
        await authenticated_user.goto(f"{base_url}/settings")

        # Wait for settings page to load
        await expect(authenticated_user.locator('[data-testid="settings-header"]')).to_be_visible(
            timeout=5000
        )

        # Verify logout button is visible and accessible
        logout_button = authenticated_user.locator('[data-testid="logout-button"]')
        await expect(logout_button).to_be_visible(timeout=2000)

        # Click logout button (HTMX POST to /auth/logout)
        await logout_button.click()

        # Should redirect to login page
        await authenticated_user.wait_for_url(f"{base_url}/login", timeout=5000)

        # Verify we're on login page
        await expect(authenticated_user.locator('[data-testid="login-form"]')).to_be_visible()

        # Verify session is cleared - accessing protected route should redirect to login
        await authenticated_user.goto(f"{base_url}/settings")
        await authenticated_user.wait_for_url(f"{base_url}/login", timeout=5000)


class TestSettingsNavigation:
    """Users should be able to navigate between chat and settings pages."""

    async def test_navigate_from_settings_to_chat(self, authenticated_user: Page, base_url: str):
        """
        Verify navigation from settings back to chat page.

        Expected behavior:
        1. User navigates to settings page
        2. Settings page loads with all cards visible
        3. User clicks "Back to Chat" link
        4. Chat page loads successfully
        """
        # Navigate to settings page
        await authenticated_user.goto(f"{base_url}/settings")

        # Wait for settings page to load
        await expect(authenticated_user.locator('[data-testid="settings-header"]')).to_be_visible(
            timeout=5000
        )

        # Verify settings page loaded with all cards
        await expect(authenticated_user.locator('[data-testid="card-garmin"]')).to_be_visible()
        await expect(authenticated_user.locator('[data-testid="card-profile"]')).to_be_visible()

        # Navigate back to chat via "Back to Chat" link
        back_to_chat_link = authenticated_user.locator('[data-testid="link-back-to-chat"]')
        await expect(back_to_chat_link).to_be_visible(timeout=2000)
        await back_to_chat_link.click()

        # Should navigate to chat page
        await authenticated_user.wait_for_url(f"{base_url}/chat/", timeout=5000)

        # Verify chat page loaded successfully
        await expect(authenticated_user.locator('[data-testid="chat-header"]')).to_be_visible()
        await expect(authenticated_user.locator("text=Conversations")).to_be_visible(timeout=2000)
