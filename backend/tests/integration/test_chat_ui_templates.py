"""Integration tests for chat UI templates and components.

Tests template rendering for:
- Garmin connection banner (Phase 3)
- Settings page components (Phase 2)
"""

from fastapi.testclient import TestClient


# Phase 3: Garmin Banner Tests
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


class TestLoginHandler:
    """Tests for login handler localStorage clearing."""

    def test_login_clears_localstorage_on_page_load(self, client: TestClient):
        """Login page should clear banner dismissed state on load."""
        response = client.get("/")
        assert response.status_code == 200
        # Script should contain removeItem for banner dismissed state
        assert "removeItem" in response.text
        assert "garmin-banner-dismissed" in response.text


# Phase 2: Settings Page Tests
def test_settings_page_renders_with_user_context(client: TestClient, test_user_token: str) -> None:
    """Settings page should render for authenticated user."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert "Settings" in response.text
    assert "Back to Chat" in response.text
    assert 'data-testid="settings-header"' in response.text


def test_settings_shows_garmin_connected(
    client_linked_garmin: TestClient,
) -> None:
    """Verify settings page displays 'Connected' status when user has linked Garmin account."""
    response = client_linked_garmin.get("/settings")

    assert response.status_code == 200
    assert "Connected" in response.text
    assert 'data-testid="garmin-status-connected"' in response.text


def test_settings_shows_garmin_not_connected(client: TestClient, test_user_token: str) -> None:
    """Verify settings page displays 'Not connected' status when user hasn't linked Garmin account."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert "Not connected" in response.text
    assert 'data-testid="garmin-status-not-connected"' in response.text


def test_settings_has_navigation_links(client: TestClient, test_user_token: str) -> None:
    """Verify settings page includes navigation links (back to chat, manage Garmin)."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    # Back to Chat link
    assert 'href="/chat/"' in response.text
    assert 'data-testid="link-back-to-chat"' in response.text
    # Garmin manage link
    assert 'href="/garmin/link"' in response.text
    assert 'data-testid="link-manage-garmin"' in response.text


def test_garmin_card_connected(
    client_linked_garmin: TestClient,
) -> None:
    """Verify Garmin card displays 'Connected' status with appropriate UI elements when linked."""
    response = client_linked_garmin.get("/settings")

    assert response.status_code == 200
    assert 'data-testid="card-garmin"' in response.text
    assert 'data-testid="garmin-status-connected"' in response.text
    assert "Connected" in response.text


def test_garmin_card_not_connected(client: TestClient, test_user_token: str) -> None:
    """Verify Garmin card displays 'Not connected' status when account is not linked."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert 'data-testid="card-garmin"' in response.text
    assert 'data-testid="garmin-status-not-connected"' in response.text
    assert "Not connected" in response.text


def test_garmin_card_has_manage_link(client: TestClient, test_user_token: str) -> None:
    """Garmin card should include 'Manage' link to /garmin/link."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert 'data-testid="link-manage-garmin"' in response.text
    assert 'href="/garmin/link"' in response.text
    assert "Manage" in response.text


def test_profile_card_shows_email(
    client: TestClient, test_user_token: str, test_user_email: str
) -> None:
    """Verify profile card displays the user's email address."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert 'data-testid="card-profile"' in response.text
    assert 'data-testid="profile-email"' in response.text
    assert test_user_email in response.text


def test_profile_card_has_edit_link(client: TestClient, test_user_token: str) -> None:
    """Profile card should include 'Edit' link with 'Coming Soon' badge."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert 'data-testid="link-edit-profile"' in response.text
    assert 'href="#"' in response.text
    assert "Edit" in response.text
    assert "Coming Soon" in response.text
    assert "onclick" in response.text


# Phase 4: Chat Header Navigation Tests
class TestChatHeaderNavigation:
    """Tests for chat header navigation elements."""

    def test_chat_header_has_settings_icon_link(self, client: TestClient, test_user_token: str):
        """Chat header should include settings icon link to /settings."""
        response = client.get("/chat/", cookies={"access_token": f"Bearer {test_user_token}"})
        assert response.status_code == 200
        assert 'data-testid="link-settings"' in response.text
        assert 'href="/settings"' in response.text
        # Check for aria-label for accessibility
        assert 'aria-label="Settings"' in response.text

    def test_chat_header_no_longer_has_dashboard_link(
        self, client: TestClient, test_user_token: str
    ):
        """Chat header should NOT include 'Dashboard' text link."""
        response = client.get("/chat/", cookies={"access_token": f"Bearer {test_user_token}"})
        assert response.status_code == 200
        # Should not have a link with text "Dashboard" in the header
        # Note: We're checking the header doesn't contain a dashboard link
        header_section = response.text.split('data-testid="chat-header"')[1].split("</header>")[0]
        assert 'href="/dashboard"' not in header_section
