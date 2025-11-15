"""Integration tests for chat UI templates.

Tests the rendering of settings.html template with various user states.
"""

from fastapi.testclient import TestClient


def test_settings_page_renders_with_user_context(client: TestClient, test_user_token: str) -> None:
    """Settings page should render for authenticated user."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert "Settings" in response.text
    assert "Back to Chat" in response.text
    assert 'data-testid="settings-header"' in response.text


def test_settings_page_displays_garmin_connection_status_connected(
    client_linked_garmin: TestClient,
) -> None:
    """Settings page should show 'Connected' when user has linked Garmin."""
    response = client_linked_garmin.get("/settings")

    assert response.status_code == 200
    assert "Connected" in response.text
    assert 'data-testid="garmin-status-connected"' in response.text


def test_settings_page_displays_garmin_connection_status_not_connected(
    client: TestClient, test_user_token: str
) -> None:
    """Settings page should show 'Not connected' when user hasn't linked Garmin."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert "Not connected" in response.text
    assert 'data-testid="garmin-status-not-connected"' in response.text


def test_settings_page_has_navigation_links(client: TestClient, test_user_token: str) -> None:
    """Settings page should include navigation links."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    # Back to Chat link
    assert 'href="/chat/"' in response.text
    assert 'data-testid="link-back-to-chat"' in response.text
    # Garmin manage link
    assert 'href="/garmin/link"' in response.text
    assert 'data-testid="link-manage-garmin"' in response.text


def test_garmin_card_shows_connected_status(
    client_linked_garmin: TestClient,
) -> None:
    """Garmin card should display green checkmark and 'Connected' when linked."""
    response = client_linked_garmin.get("/settings")

    assert response.status_code == 200
    assert 'data-testid="card-garmin"' in response.text
    assert 'data-testid="garmin-status-connected"' in response.text
    assert "Connected" in response.text


def test_garmin_card_shows_not_connected_status(client: TestClient, test_user_token: str) -> None:
    """Garmin card should display 'Not connected' when not linked."""
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


def test_profile_card_displays_user_email(
    client: TestClient, test_user_token: str, test_user_email: str
) -> None:
    """Profile card should display user's email address."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert 'data-testid="card-profile"' in response.text
    assert 'data-testid="profile-email"' in response.text
    assert test_user_email in response.text


def test_profile_card_has_edit_link(client: TestClient, test_user_token: str) -> None:
    """Profile card should include 'Edit' link to /profile/edit."""
    response = client.get("/settings", cookies={"access_token": f"Bearer {test_user_token}"})

    assert response.status_code == 200
    assert 'data-testid="link-edit-profile"' in response.text
    assert 'href="/profile/edit"' in response.text
    assert "Edit" in response.text
