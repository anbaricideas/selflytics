"""Integration tests for authentication middleware and 401 exception handling.

Tests verify that 401 Unauthorized errors are handled differently for:
- Browser requests (Accept: text/html) → Redirect to /login
- HTMX requests (HX-Request: true) → Redirect to /login
- API requests (no Accept header) → FastAPI raises HTTPException
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


@pytest.fixture(autouse=True)
def bypass_csrf_for_auth_middleware_tests(monkeypatch):
    """Bypass CSRF validation for these auth middleware tests.

    CSRF-specific tests are in test_csrf_routes.py.
    These tests focus on authentication middleware, not CSRF protection.
    """

    async def mock_validate_csrf(self, request):
        pass  # Bypass CSRF validation

    monkeypatch.setattr(
        "fastapi_csrf_protect.flexible.CsrfProtect.validate_csrf", mock_validate_csrf
    )


def test_401_with_browser_accept_header_redirects_to_login(unauthenticated_client):
    """Browser request (Accept: text/html) receiving 401 should redirect to /login."""
    response = unauthenticated_client.get(
        "/garmin/link",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )

    # Should return 303 See Other redirect to /login
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"


def test_401_with_htmx_request_header_redirects_to_login(unauthenticated_client):
    """HTMX request receiving 401 should redirect to /login."""
    response = unauthenticated_client.get(
        "/garmin/link",
        headers={
            "HX-Request": "true",
            "Accept": "text/html",
        },
        follow_redirects=False,
    )

    # HTMX requests with 401 should redirect to login
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"


def test_401_without_browser_headers_returns_json_error(unauthenticated_client):
    """API request without browser headers receiving 401 should return JSON error."""
    # Without Accept: text/html or HX-Request, the exception handler returns JSON
    response = unauthenticated_client.get("/garmin/link")

    # Verify response is 401 with JSON error
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_dashboard_without_auth_redirects_to_settings(unauthenticated_client):
    """Dashboard GET redirects to settings (Phase 1 - chat-first navigation)."""
    response = unauthenticated_client.get(
        "/dashboard",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )

    # Dashboard now redirects to /settings (301 permanent) - no auth required for redirect
    assert response.status_code == 301
    assert response.headers["location"] == "/settings"


def test_protected_post_without_auth_redirects_browser(unauthenticated_client):
    """Protected POST endpoint without auth should redirect browser requests."""
    response = unauthenticated_client.post(
        "/garmin/link",
        data={
            "username": "test@garmin.com",
            "password": "password123",
        },
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )

    # Browser POST without auth should redirect to login
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"


def test_htmx_post_without_auth_redirects_to_login(unauthenticated_client):
    """HTMX POST without auth should redirect to /login."""
    response = unauthenticated_client.post(
        "/garmin/link",
        data={
            "username": "test@garmin.com",
            "password": "password123",
        },
        headers={
            "HX-Request": "true",
            "Accept": "text/html",
        },
        follow_redirects=False,
    )

    # HTMX POST without auth should redirect
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"


def test_other_http_exceptions_not_affected(client, test_user_token):
    """Non-401 HTTP exceptions should behave normally (not redirect)."""
    # Trigger a 400 Bad Request by sending invalid form data
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.link_account.return_value = False  # Triggers 400 error
        mock_service_class.return_value = mock_service

        response = client.post(
            "/garmin/link",
            data={
                "username": "invalid",
                "password": "wrong",
            },
            headers={
                "Authorization": f"Bearer {test_user_token}",
                "Accept": "text/html",
            },
            follow_redirects=False,
        )

        # Should return 400 error, NOT redirect
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Should NOT redirect to /login
        assert response.headers.get("location") != "/login"


def test_authenticated_request_does_not_redirect(client, test_user_token):
    """Authenticated request should not redirect even with text/html Accept."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.link_account.return_value = True
        mock_service_class.return_value = mock_service

        response = client.post(
            "/garmin/link",
            data={
                "username": "test@garmin.com",
                "password": "password123",
            },
            headers={
                "Authorization": f"Bearer {test_user_token}",
                "Accept": "text/html",
            },
            follow_redirects=False,
        )

        # Should return 200 success, NOT redirect
        assert response.status_code == status.HTTP_200_OK
        # Should NOT have redirect
        assert "location" not in response.headers
