"""Integration tests for HTMX-specific authentication behaviors.

Tests verify that auth endpoints correctly:
- Return HX-Redirect headers for HTMX requests
- Return HTML fragments for validation errors
- Return JSON for non-HTMX API requests
"""

from unittest.mock import AsyncMock

from fastapi import status

from app.auth.dependencies import get_user_service
from app.auth.password import hash_password
from app.main import app


def test_register_success_returns_hx_redirect_header(
    unauthenticated_client, create_mock_user, mock_user_service_override
):
    """POST /auth/register success with HX-Request header should return HX-Redirect to /dashboard."""
    # Mock user service without conflicting with fixture
    mock_svc = AsyncMock()
    mock_svc.get_user_by_email.return_value = None  # No existing user
    mock_svc.create_user.return_value = create_mock_user(
        user_id="new-user-123",
        email="newuser@example.com",
    )

    with mock_user_service_override(mock_svc):
        response = unauthenticated_client.post(
            "/auth/register",
            data={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "display_name": "New User",
                "confirm_password": "SecurePass123!",
            },
            headers={"HX-Request": "true"},
        )

        # HTMX redirects use status 200 with HX-Redirect header (not 302)
        assert response.status_code == status.HTTP_200_OK
        assert "HX-Redirect" in response.headers
        assert response.headers["HX-Redirect"] == "/dashboard"

        # Should set authentication cookie
        assert "access_token" in response.cookies
        # Cookie attributes are set correctly (verified by e2e tests)


def test_register_success_without_htmx_returns_json(unauthenticated_client, create_mock_user):
    """POST /auth/register success without HX-Request should return JSON response."""
    mock_svc = AsyncMock()
    mock_svc.get_user_by_email.return_value = None
    mock_svc.create_user.return_value = create_mock_user(
        user_id="new-user-456",
        email="apiuser@example.com",
    )

    app.dependency_overrides[get_user_service] = lambda: mock_svc

    try:
        response = unauthenticated_client.post(
            "/auth/register",
            data={
                "email": "apiuser@example.com",
                "password": "SecurePass123!",
                "display_name": "API User",
            },
            # No HX-Request header
        )

        # API requests return 201 Created with JSON body
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "apiuser@example.com"
        assert data["user_id"] == "new-user-456"

        # Should NOT have HX-Redirect header
        assert "HX-Redirect" not in response.headers

    finally:
        app.dependency_overrides.clear()


def test_register_validation_error_returns_html_fragment(unauthenticated_client, create_mock_user):
    """POST /auth/register with HTMX and validation error should return HTML error fragment."""
    mock_svc = AsyncMock()
    # Mock existing user to trigger "email already registered" error
    mock_svc.get_user_by_email.return_value = create_mock_user(
        user_id="existing-user",
        email="existing@example.com",
    )

    app.dependency_overrides[get_user_service] = lambda: mock_svc

    try:
        response = unauthenticated_client.post(
            "/auth/register",
            data={
                "email": "existing@example.com",
                "password": "SecurePass123!",
                "display_name": "Duplicate",
            },
            headers={"HX-Request": "true"},
        )

        # Should return 400 with HTML content
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "text/html" in response.headers.get("content-type", "")

        # Should contain specific error message
        html = response.text
        assert "Email already registered" in html

    finally:
        app.dependency_overrides.clear()


def test_register_password_mismatch_returns_html_error(unauthenticated_client):
    """POST /auth/register with HTMX and password mismatch should return HTML error."""
    response = unauthenticated_client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword!",
            "display_name": "Test User",
        },
        headers={"HX-Request": "true"},
    )

    # Should return 400 with HTML error fragment
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "text/html" in response.headers.get("content-type", "")

    # Should mention password mismatch
    html = response.text
    assert "password" in html.lower()


def test_login_success_returns_hx_redirect_header(unauthenticated_client, create_mock_user):
    """POST /auth/login success with HX-Request should return HX-Redirect to /dashboard."""
    mock_svc = AsyncMock()
    mock_user = create_mock_user(
        user_id="login-user-123",
        email="loginuser@example.com",
        hashed_password=hash_password("CorrectPassword123!"),
    )
    mock_svc.get_user_by_email.return_value = mock_user

    app.dependency_overrides[get_user_service] = lambda: mock_svc

    try:
        response = unauthenticated_client.post(
            "/auth/login",
            data={
                "username": "loginuser@example.com",  # OAuth2 uses 'username' field
                "password": "CorrectPassword123!",
            },
            headers={"HX-Request": "true"},
        )

        # Should return 200 with HX-Redirect header
        assert response.status_code == status.HTTP_200_OK
        assert "HX-Redirect" in response.headers
        assert response.headers["HX-Redirect"] == "/dashboard"

        # Should set authentication cookie
        assert "access_token" in response.cookies

    finally:
        app.dependency_overrides.clear()


def test_login_invalid_credentials_returns_html_error(unauthenticated_client, create_mock_user):
    """POST /auth/login with HTMX and wrong password should return HTML error fragment."""
    mock_svc = AsyncMock()
    mock_user = create_mock_user(
        user_id="user-123",
        email="user@example.com",
        hashed_password=hash_password("ActualPassword"),
    )
    mock_svc.get_user_by_email.return_value = mock_user

    app.dependency_overrides[get_user_service] = lambda: mock_svc

    try:
        response = unauthenticated_client.post(
            "/auth/login",
            data={
                "username": "user@example.com",
                "password": "WrongPassword",
            },
            headers={"HX-Request": "true"},
        )

        # Should return 401 with HTML error
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "text/html" in response.headers.get("content-type", "")

        # Should contain generic error message (without exposing which field is wrong)
        html = response.text.lower()
        assert "incorrect" in html or "invalid" in html

        # Should NOT expose which specific field was wrong (prevents user enumeration)
        assert "password incorrect" not in html
        assert "username not found" not in html
        assert "email not found" not in html

    finally:
        app.dependency_overrides.clear()


def test_login_success_without_htmx_returns_json(unauthenticated_client, create_mock_user):
    """POST /auth/login success without HX-Request should return JSON with access token."""
    mock_svc = AsyncMock()
    mock_user = create_mock_user(
        user_id="api-login-user",
        email="apilogin@example.com",
        hashed_password=hash_password("Password123!"),
    )
    mock_svc.get_user_by_email.return_value = mock_user

    app.dependency_overrides[get_user_service] = lambda: mock_svc

    try:
        response = unauthenticated_client.post(
            "/auth/login",
            data={
                "username": "apilogin@example.com",
                "password": "Password123!",
            },
            # No HX-Request header
        )

        # API requests return 200 with JSON access token
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"  # noqa: S105

        # Should NOT have HX-Redirect header
        assert "HX-Redirect" not in response.headers

    finally:
        app.dependency_overrides.clear()
