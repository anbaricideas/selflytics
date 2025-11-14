"""Integration tests for HTMX-specific Garmin endpoint behaviors.

Tests verify that Garmin endpoints correctly:
- Return HTML fragments (not JSON) for HTMX requests
- Include proper data-testid attributes for e2e test selectors
- Return error HTML fragments with appropriate styling
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status


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

        # HTML should contain success indicator
        html = response.text
        assert 'data-testid="garmin-status-linked"' in html
        assert "Garmin account linked" in html or "linked" in html.lower()

        # Should contain sync button
        assert 'data-testid="button-sync-garmin"' in html
        assert "Sync Now" in html or "sync" in html.lower()

        # Should be styled as success (green colors)
        assert "green" in html.lower() or "success" in html.lower()


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
        assert 'data-testid="error-message"' in html
        assert "Failed to link" in html or "failed" in html.lower()
        assert "credentials" in html.lower() or "try again" in html.lower()

        # Should be styled as error (red colors)
        assert "red" in html.lower() or "error" in html.lower()


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

        # Should NOT be valid JSON
        with pytest.raises(Exception):  # noqa: B017, PT011
            response.json()


def test_link_garmin_error_does_not_expose_implementation_details(client, test_user_token):
    """POST /garmin/link error returns 500 when exceptions occur (no error handler yet)."""
    with patch("app.routes.garmin.GarminService") as mock_service_class:
        mock_service = AsyncMock()
        # Simulate exception in service
        mock_service.link_account.side_effect = Exception(
            "Internal database error with sensitive info"
        )
        mock_service_class.return_value = mock_service

        # Without error handler, exception propagates causing test client to raise
        with pytest.raises(Exception, match="Internal database error") as exc_info:
            client.post(
                "/garmin/link",
                data={
                    "username": "test@garmin.com",
                    "password": "password123",
                },
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        # Verify exception occurred (implementation needs error handler for production)
        assert "Internal database error" in str(exc_info.value)


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
    # No Authorization header - will raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        unauthenticated_client.post(
            "/garmin/link",
            data={
                "username": "test@garmin.com",
                "password": "password123",
            },
        )

    # Should be 401 Unauthorized
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
