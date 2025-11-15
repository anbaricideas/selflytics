"""Integration tests for CSRF protection on routes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User, UserProfile
from app.services.garmin_service import GarminService


def test_register_requires_csrf_token(client: TestClient):
    """Test that /auth/register rejects requests without CSRF token."""
    response = client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "TestPass123",
            "display_name": "Test User",
            "confirm_password": "TestPass123",
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_register_with_valid_csrf_token(client: TestClient):
    """Test that /auth/register accepts valid CSRF token."""
    # Get form with CSRF token
    form_response = client.get("/register")
    assert form_response.status_code == 200

    # Extract CSRF token from cookie (library uses 'fastapi-csrf-token' as cookie name)
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None

    # Extract CSRF token from HTML (form field name is 'csrf_token')
    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input is not None
    csrf_token = csrf_input["value"]

    # Submit form with valid token
    response = client.post(
        "/auth/register",
        data={
            "email": "newuser@example.com",
            "password": "TestPass123",
            "display_name": "New User",
            "confirm_password": "TestPass123",
            "fastapi-csrf-token": csrf_token,  # form field name
        },
        cookies={"fastapi-csrf-token": csrf_cookie},  # cookie name
    )

    # Should succeed (or fail with email exists, not CSRF error)
    assert response.status_code in (200, 400)
    if response.status_code == 400:
        # If 400, should be email exists, not CSRF error
        assert "CSRF" not in response.text


def test_csrf_token_rotation_on_register_error(client: TestClient):
    """Test that CSRF token is rotated when registration has validation errors."""
    # Get initial form
    form1 = client.get("/register")
    cookie1 = form1.cookies.get("fastapi-csrf-token")

    soup = BeautifulSoup(form1.text, "html.parser")
    csrf_token1 = soup.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit with password mismatch error
    response = client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "Pass123",
            "confirm_password": "Pass456",  # Mismatch!
            "display_name": "Test",
            "fastapi-csrf-token": csrf_token1,
        },
        cookies={"fastapi-csrf-token": cookie1},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 400
    assert "Passwords do not match" in response.text

    # Token should be rotated
    cookie2 = response.cookies.get("fastapi-csrf-token")
    assert cookie2 is not None
    assert cookie2 != cookie1  # Different cookie!

    # Extract new token from returned form fragment
    soup2 = BeautifulSoup(response.text, "html.parser")
    csrf_input2 = soup2.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input2 is not None
    csrf_token2 = csrf_input2["value"]
    assert csrf_token2 != csrf_token1  # Different token value!


def test_login_requires_csrf_token(client: TestClient):
    """Test that /auth/login rejects requests without CSRF token."""
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123",
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_login_with_valid_csrf_token(client: TestClient):
    """Test that /auth/login accepts valid CSRF token."""
    # Get form with CSRF token
    form_response = client.get("/login")
    assert form_response.status_code == 200

    # Extract CSRF token
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit with valid token (will fail auth but not CSRF)
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "WrongPassword",
            "fastapi-csrf-token": csrf_token,
        },
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    # Should fail auth (401 or 400), not CSRF (403)
    assert response.status_code in (400, 401)
    assert "CSRF" not in response.text


def test_csrf_token_rotation_on_login_error(client: TestClient):
    """Test that CSRF token is rotated on login failure."""
    # Get initial form
    form1 = client.get("/login")
    cookie1 = form1.cookies.get("fastapi-csrf-token")
    soup1 = BeautifulSoup(form1.text, "html.parser")
    csrf_token1 = soup1.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit with wrong credentials
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "WrongPassword",
            "fastapi-csrf-token": csrf_token1,
        },
        cookies={"fastapi-csrf-token": cookie1},
        headers={"HX-Request": "true"},
    )

    assert response.status_code in (400, 401)

    # Token should be rotated
    cookie2 = response.cookies.get("fastapi-csrf-token")
    assert cookie2 is not None
    assert cookie2 != cookie1

    # Extract new token from form
    soup2 = BeautifulSoup(response.text, "html.parser")
    csrf_input2 = soup2.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input2 is not None
    csrf_token2 = csrf_input2["value"]
    assert csrf_token2 != csrf_token1


@pytest.fixture
def test_garmin_user():
    """Create a test user for Garmin tests."""
    return User(
        user_id="test-garmin-user-123",
        email="garmin@example.com",
        hashed_password="$2b$12$test",  # noqa: S106
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        profile=UserProfile(display_name="Garmin Test User"),
        garmin_linked=False,
    )


@pytest.fixture
def mock_garmin_service():
    """Provide mocked GarminService."""
    mock = Mock(spec=GarminService)
    # Always fail link_account to test error path
    mock.link_account = AsyncMock(return_value=False)
    mock.sync_recent_data = AsyncMock()
    return mock


@pytest.fixture
def mock_garmin_service_sync_failure():
    """Provide mocked GarminService with sync_recent_data that raises exception."""
    mock = Mock(spec=GarminService)
    mock.link_account = AsyncMock(return_value=True)
    # Force sync to fail with exception
    mock.sync_recent_data = AsyncMock(side_effect=Exception("Sync failed"))
    return mock


@pytest.fixture
def authenticated_garmin_client(test_garmin_user, mock_garmin_service, monkeypatch):
    """Provide a TestClient with authenticated user for Garmin tests.

    Cleanup handled by autouse reset_app_state fixture.
    """

    # Mock get_current_user to return test user
    async def mock_get_current_user():
        return test_garmin_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    # Mock GarminService instantiation
    def mock_garmin_service_init(user_id: str):
        mock_garmin_service.user_id = user_id
        return mock_garmin_service

    monkeypatch.setattr("app.routes.garmin.GarminService", mock_garmin_service_init)

    return TestClient(app, raise_server_exceptions=False)


def test_garmin_link_requires_csrf_token(authenticated_garmin_client: TestClient):
    """Test that /garmin/link rejects requests without CSRF token."""
    response = authenticated_garmin_client.post(
        "/garmin/link",
        data={
            "username": "test@garmin.com",
            "password": "GarminPass123",
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_garmin_link_with_valid_csrf_token(authenticated_garmin_client: TestClient):
    """Test that /garmin/link accepts valid CSRF token."""
    # Get form with CSRF token
    form_response = authenticated_garmin_client.get("/garmin/link")
    assert form_response.status_code == 200

    # Extract CSRF token
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None

    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input is not None
    csrf_token = csrf_input["value"]

    # Submit with valid token (may fail auth, but not CSRF)
    response = authenticated_garmin_client.post(
        "/garmin/link",
        data={
            "username": "test@garmin.com",
            "password": "WrongGarminPass",
            "fastapi-csrf-token": csrf_token,
        },
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    # Should fail Garmin auth (400), not CSRF (403)
    assert response.status_code in (200, 400, 500)
    assert response.status_code != 403  # Not CSRF error


def test_csrf_token_rotation_on_garmin_link_error(authenticated_garmin_client: TestClient):
    """Test that CSRF token is rotated when Garmin link fails."""
    # Get initial form
    form1 = authenticated_garmin_client.get("/garmin/link")
    token1 = form1.cookies.get("fastapi-csrf-token")
    soup1 = BeautifulSoup(form1.text, "html.parser")
    csrf_token1 = soup1.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit with wrong credentials (will fail)
    response = authenticated_garmin_client.post(
        "/garmin/link",
        data={
            "username": "test@garmin.com",
            "password": "WrongPassword",
            "fastapi-csrf-token": csrf_token1,
        },
        cookies={"fastapi-csrf-token": token1},
        headers={"HX-Request": "true"},
    )

    assert response.status_code in (400, 500)

    # Token should be rotated
    token2 = response.cookies.get("fastapi-csrf-token")
    assert token2 is not None
    assert token2 != token1

    # Extract new token from form
    soup2 = BeautifulSoup(response.text, "html.parser")
    csrf_input2 = soup2.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input2 is not None
    csrf_token2 = csrf_input2["value"]
    assert csrf_token2 != csrf_token1


def test_garmin_sync_requires_csrf_token(authenticated_garmin_client: TestClient):
    """Test that /garmin/sync rejects requests without CSRF token."""
    response = authenticated_garmin_client.post(
        "/garmin/sync",
        data={
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_garmin_sync_with_valid_csrf_token(authenticated_garmin_client: TestClient):
    """Test that /garmin/sync accepts valid CSRF token.

    Note: This test may fail with 500 (no linked account) but should not fail with 403 (CSRF).
    """
    # Get a CSRF token (from link page)
    form_response = authenticated_garmin_client.get("/garmin/link")
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit sync with valid CSRF token
    response = authenticated_garmin_client.post(
        "/garmin/sync",
        data={
            "fastapi-csrf-token": csrf_token,
        },
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    # Should fail business logic (500), not CSRF (403)
    assert response.status_code in (200, 400, 500)
    assert response.status_code != 403


def test_csrf_token_rotation_on_garmin_sync_error(
    test_garmin_user, mock_garmin_service_sync_failure, monkeypatch
):
    """Test that CSRF token is rotated when Garmin sync fails."""

    # Create authenticated client with sync failure mock
    async def mock_get_current_user():
        return test_garmin_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    def mock_garmin_service_init(user_id: str):
        mock_garmin_service_sync_failure.user_id = user_id
        return mock_garmin_service_sync_failure

    monkeypatch.setattr("app.routes.garmin.GarminService", mock_garmin_service_init)

    client = TestClient(app, raise_server_exceptions=False)

    # Get initial CSRF token
    form_response = client.get("/garmin/link")
    token1 = form_response.cookies.get("fastapi-csrf-token")
    soup1 = BeautifulSoup(form_response.text, "html.parser")
    csrf_token1 = soup1.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit sync request that will fail
    response = client.post(
        "/garmin/sync",
        data={
            "fastapi-csrf-token": csrf_token1,
        },
        cookies={"fastapi-csrf-token": token1},
        headers={"HX-Request": "true"},
    )

    # Should return 500 error
    assert response.status_code == 500

    # Token should be rotated
    token2 = response.cookies.get("fastapi-csrf-token")
    assert token2 is not None
    assert token2 != token1

    # Clean up override
    app.dependency_overrides.clear()


def test_garmin_unlink_requires_csrf_token(authenticated_garmin_client: TestClient):
    """Test that DELETE /garmin/link rejects requests without CSRF token."""
    response = authenticated_garmin_client.delete("/garmin/link")

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_garmin_unlink_rejects_invalid_csrf_token_in_header(
    authenticated_garmin_client: TestClient,
):
    """Test that DELETE /garmin/link rejects invalid CSRF token in header."""
    # Get CSRF cookie (but don't use the correct token)
    form_response = authenticated_garmin_client.get("/garmin/link")
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None

    # Submit DELETE with INVALID token in header
    response = authenticated_garmin_client.delete(
        "/garmin/link",
        cookies={"fastapi-csrf-token": csrf_cookie},
        headers={"X-CSRF-Token": "invalid-token-12345"},
    )

    # Should fail CSRF validation (403)
    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_garmin_unlink_with_valid_csrf_token(authenticated_garmin_client: TestClient):
    """Test that DELETE /garmin/link accepts valid CSRF token in header."""
    # Get CSRF token (from link page)
    form_response = authenticated_garmin_client.get("/garmin/link")
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None

    # Extract unsigned CSRF token from HTML form
    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit DELETE with valid CSRF token in header
    response = authenticated_garmin_client.delete(
        "/garmin/link",
        cookies={"fastapi-csrf-token": csrf_cookie},
        headers={"X-CSRF-Token": csrf_token},  # Send unsigned token in header
    )

    # Should succeed (200) or fail business logic (500), not CSRF (403)
    assert response.status_code in (200, 500)
    assert response.status_code != 403


@pytest.fixture
def test_logout_user():
    """Create a test user for logout tests."""
    return User(
        user_id="test-logout-user-123",
        email="logout_test@example.com",
        hashed_password="$2b$12$test",  # noqa: S106
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        profile=UserProfile(display_name="Logout Test User"),
        garmin_linked=False,
    )


@pytest.fixture
def authenticated_logout_client(test_logout_user):
    """Provide TestClient with authenticated session for logout testing.

    Uses dependency override to mock authentication.
    Cleanup handled by autouse reset_app_state fixture.
    """

    # Mock get_current_user to return test user
    async def mock_get_current_user():
        return test_logout_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    return TestClient(app, raise_server_exceptions=False)


def test_logout_requires_csrf_token(authenticated_logout_client: TestClient):
    """Test that POST /logout rejects requests without CSRF token."""
    response = authenticated_logout_client.post(
        "/logout",
        # csrf_token intentionally omitted
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_logout_with_valid_csrf_token(authenticated_logout_client: TestClient):
    """Test that POST /logout succeeds with valid CSRF token."""
    # Get settings page to obtain CSRF token
    settings_response = authenticated_logout_client.get("/settings")
    assert settings_response.status_code == 200

    # Extract CSRF token from cookie
    csrf_cookie = settings_response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None

    # Extract CSRF token from HTML hidden input
    soup = BeautifulSoup(settings_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input is not None
    csrf_token = csrf_input["value"]

    # Logout with valid CSRF token
    response = authenticated_logout_client.post(
        "/logout",
        data={"fastapi-csrf-token": csrf_token},
        cookies={"fastapi-csrf-token": csrf_cookie},
        follow_redirects=False,
    )

    # Should succeed with redirect to login
    assert response.status_code == 303
    assert response.headers["Location"] == "/login"

    # Verify access_token cookie is cleared (deleted)
    set_cookie_header = response.headers.get("Set-Cookie", "")
    assert "access_token" in set_cookie_header or "access_token" in response.cookies
    # Cookie should be deleted (empty value or Max-Age=0)
    assert response.cookies.get("access_token") == "" or "Max-Age=0" in set_cookie_header, (
        "access_token cookie should be deleted on logout"
    )


def test_logout_failed_attempt_preserves_session(authenticated_logout_client: TestClient):
    """Test that failed logout (no CSRF token) preserves user session."""
    # Attempt logout WITHOUT CSRF token (attack scenario)
    response = authenticated_logout_client.post("/logout")

    # Should fail with 403
    assert response.status_code == 403

    # Verify user is STILL authenticated by accessing protected page
    chat_response = authenticated_logout_client.get("/chat/")

    # Should succeed (200), not redirect to login
    assert chat_response.status_code == 200

    # Page should contain logout button (user still logged in)
    assert 'action="/logout"' in chat_response.text
    assert "logout-button" in chat_response.text


def test_logout_with_invalid_token(authenticated_logout_client: TestClient):
    """Test that POST /logout rejects invalid CSRF token."""
    # Get legitimate CSRF token first (to get cookie)
    settings_response = authenticated_logout_client.get("/settings")
    csrf_cookie = settings_response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None

    # Use TAMPERED token (not the real one from HTML)
    tampered_token = "tampered_invalid_token_12345"  # noqa: S105

    # Attempt logout with tampered token
    response = authenticated_logout_client.post(
        "/logout",
        data={"fastapi-csrf-token": tampered_token},
        cookies={"fastapi-csrf-token": csrf_cookie},
        follow_redirects=False,
    )

    # Should fail CSRF validation
    assert response.status_code == 403
