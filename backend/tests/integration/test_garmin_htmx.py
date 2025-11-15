"""Integration tests for HTMX-specific Garmin endpoint behaviors.

Tests verify that Garmin endpoints correctly:
- Return HTML fragments (not JSON) for HTMX requests
- Include proper data-testid attributes for e2e test selectors
- Return error HTML fragments with appropriate styling
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


@pytest.fixture(autouse=True)
def bypass_csrf_for_garmin_tests(monkeypatch):
    """Bypass CSRF validation for these Garmin HTMX tests.

    CSRF-specific tests are in test_csrf_routes.py.
    These tests focus on HTMX behavior, not CSRF protection.
    """

    async def mock_validate_csrf(self, request):
        pass  # Bypass CSRF validation

    monkeypatch.setattr("fastapi_csrf_protect.CsrfProtect.validate_csrf", mock_validate_csrf)


def test_link_garmin_success_returns_html_fragment(client, test_user_token):
    """POST /garmin/link success should return HTML fragment with linked status."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.link_account.return_value = True  # Success
        mock_service_class.return_value = mock_service

        response = client.post(
            "/garmin/link",
            data={
                "username": "test@garmin.com",
                "password": "password123",
            },
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Should return 200 with HTML content
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")

        # Verify meaningful behavior: user can see status and proceed to sync
        html = response.text
        assert 'data-testid="garmin-status-linked"' in html, "Missing linked status indicator"
        assert "Garmin account linked" in html, "Missing success message"
        assert 'data-testid="button-sync-garmin"' in html, "Missing sync action button"

        # Visual styling is verified by e2e tests and manual QA


def test_link_garmin_failure_returns_html_error_fragment(client, test_user_token):
    """POST /garmin/link failure should return HTML error fragment."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.link_account.return_value = False  # Failure
        mock_service_class.return_value = mock_service

        response = client.post(
            "/garmin/link",
            data={
                "username": "wrong@garmin.com",
                "password": "wrongpassword",
            },
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Should return 400 with HTML error content
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "text/html" in response.headers.get("content-type", "")

        # HTML should contain error message
        html = response.text
        assert 'data-testid="error-message"' in html, "Missing error message container"
        assert any(
            phrase in html.lower()
            for phrase in ["failed to link", "invalid credentials", "could not link"]
        ), "Missing user-friendly error message"

        # Should allow user to retry (form or HTMX trigger available)
        # Visual styling (red/error colors) verified by e2e tests


def test_link_garmin_response_is_html_not_json(client, test_user_token):
    """POST /garmin/link should return HTML, not JSON."""
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
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Must be HTML, not JSON
        assert "text/html" in response.headers.get("content-type", "")
        assert "application/json" not in response.headers.get("content-type", "")

        # Should contain HTML content
        assert 'data-testid="garmin-status-linked"' in response.text


def test_link_garmin_internal_error_returns_generic_message(client, test_user_token):
    """POST /garmin/link internal error should return generic user-facing message."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        # Simulate internal error with sensitive information
        mock_service.link_account.side_effect = Exception(
            "Database connection failed: host=internal-db.prod.company.com user=admin_user"
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/garmin/link",
            data={
                "username": "test@garmin.com",
                "password": "password123",
            },
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Should return 500 with generic error message
        assert response.status_code == 500
        assert "text/html" in response.headers.get("content-type", "")

        html = response.text

        # Should NOT expose internal error details
        assert "Database connection failed" not in html
        assert "internal-db.prod.company.com" not in html
        assert "admin_user" not in html

        # Should show generic user-friendly message
        assert 'data-testid="error-message"' in html
        assert any(
            phrase in html.lower()
            for phrase in ["something went wrong", "unexpected error", "try again later"]
        )


def test_sync_garmin_success_returns_html_fragment(client, test_user_token):
    """POST /garmin/sync success should return HTML with sync status."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.sync_activities.return_value = {"synced_count": 5}
        mock_service_class.return_value = mock_service

        response = client.post(
            "/garmin/sync",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Should return 200 with HTML content
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")

        # HTML should contain success message
        html = response.text
        assert "sync" in html.lower()
        # Should indicate success or completion
        assert any(
            word in html.lower() for word in ["success", "completed", "synchronized", "synced"]
        )


def test_sync_garmin_failure_returns_html_error(client, test_user_token):
    """POST /garmin/sync failure returns HTML error fragment (has error handler)."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        # Simulate sync failure
        mock_service.sync_recent_data.side_effect = Exception("Garmin API timeout")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/garmin/sync",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Should return 500 with HTML error
        assert response.status_code == 500
        assert "text/html" in response.headers.get("content-type", "")

        html = response.text
        assert 'data-testid="sync-error"' in html
        assert "Sync failed" in html or "failed" in html.lower()


def test_garmin_endpoints_accept_form_data_not_json(client, test_user_token):
    """POST /garmin/link should accept form data (not JSON body)."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.link_account.return_value = True
        mock_service_class.return_value = mock_service

        # Send as form data (what HTMX sends)
        response = client.post(
            "/garmin/link",
            data={  # Form data
                "username": "test@garmin.com",
                "password": "password123",
            },
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        # Service should have been called with form values
        mock_service.link_account.assert_called_once_with(
            username="test@garmin.com",
            password="password123",  # noqa: S106
        )


def test_garmin_endpoints_require_authentication(unauthenticated_client):
    """Garmin endpoints should return 401 without authentication."""
    # No Authorization header - should return 401 JSON response
    response = unauthenticated_client.post(
        "/garmin/link",
        data={
            "username": "test@garmin.com",
            "password": "password123",
        },
    )

    # Should be 401 Unauthorized with JSON error
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"
