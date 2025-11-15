"""Integration tests for chat UI templates and components.

Tests template rendering for:
- Garmin connection banner (Phase 3)
- Settings page components (Phase 2)
"""

from fastapi.testclient import TestClient


class TestGarminBanner:
    """Tests for Garmin connection banner on chat page."""

    def test_banner_appears_when_garmin_not_linked(self, client: TestClient, test_user_token: str):
        """Banner should appear when user has not linked Garmin account."""
        response = client.get("/chat/", cookies={"access_token": f"Bearer {test_user_token}"})
        assert response.status_code == 200
        assert 'id="garmin-banner"' in response.text
        assert 'data-testid="garmin-banner"' in response.text

    def test_banner_has_link_to_garmin_oauth(self, client: TestClient, test_user_token: str):
        """Banner should include Link Now button to /garmin/link."""
        response = client.get("/chat/", cookies={"access_token": f"Bearer {test_user_token}"})
        assert response.status_code == 200
        assert 'href="/garmin/link"' in response.text
        assert 'data-testid="banner-link-now"' in response.text
        assert "Link Now" in response.text

    def test_banner_has_dismiss_button(self, client: TestClient, test_user_token: str):
        """Banner should include dismiss button with correct ID."""
        response = client.get("/chat/", cookies={"access_token": f"Bearer {test_user_token}"})
        assert response.status_code == 200
        assert 'id="dismiss-banner"' in response.text
        assert 'data-testid="banner-dismiss"' in response.text


class TestBannerDismissalScript:
    """Tests for banner dismissal JavaScript logic."""

    def test_banner_dismissal_script_included(self, client: TestClient, test_user_token: str):
        """Chat page should include banner dismissal script with localStorage."""
        response = client.get("/chat/", cookies={"access_token": f"Bearer {test_user_token}"})
        assert response.status_code == 200
        # Check for localStorage key used in dismissal logic
        assert "garmin-banner-dismissed" in response.text


class TestLogoutHandler:
    """Tests for logout handler localStorage clearing."""

    def test_logout_clears_localstorage_in_client(self, client: TestClient, test_user_token: str):
        """Logout handler should include localStorage.removeItem call."""
        response = client.get("/chat/", cookies={"access_token": f"Bearer {test_user_token}"})
        assert response.status_code == 200
        # Check for logout handler that clears localStorage
        assert 'action="/logout"' in response.text
        # Script should contain removeItem for banner dismissed state
        assert "removeItem" in response.text
        assert "garmin-banner-dismissed" in response.text
