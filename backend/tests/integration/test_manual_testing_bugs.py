"""Integration tests for bugs found during manual testing.

These tests capture bugs discovered during Phase 4 manual testing runsheet execution.
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


# Test data constants
TEST_GARMIN_USERNAME = "test@garmin.com"
TEST_GARMIN_PASSWORD = "password123"  # noqa: S105 - Test fixture, not a real password
INVALID_GARMIN_USERNAME = "invalid@garmin.com"
INVALID_GARMIN_PASSWORD = "wrongpassword"  # noqa: S105 - Test fixture


class TestDashboardGarminLinkRouting:
    """Test that dashboard Garmin link uses correct URL.

    Bug: Dashboard template links to /settings/garmin but route is /garmin/link
    Expected: Dashboard should link to /garmin/link (the actual route)
    """

    def test_dashboard_garmin_link_uses_correct_url(self, client: TestClient, test_user_token: str):
        """Dashboard 'Connect Now' button should link to /garmin/link, not /settings/garmin."""
        # Dashboard doesn't call GarminService, but mock for isolation
        # Use Authorization header (matches project pattern in test_garmin_htmx.py)
        response = client.get(
            "/dashboard",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 200
        html = response.text

        # The button should link to the correct route
        assert 'href="/garmin/link"' in html, (
            "Dashboard should link to /garmin/link (actual route), "
            f"not /settings/garmin (404). Found in HTML: {_show_link_context(html)}"
        )

        # Should NOT link to non-existent route
        assert 'href="/settings/garmin"' not in html, (
            "Dashboard should not link to /settings/garmin (does not exist). "
            "This causes 404 when users click 'Connect Now'."
        )


def _show_link_context(html: str, search: str = 'href="/garmin', context: int = 200) -> str:
    """Show context around link for better error messages."""
    idx = html.find(search) if search in html else html.find('href="/settings')
    if idx == -1:
        return "No Garmin links found"
    start = max(0, idx - context)
    end = min(len(html), idx + context)
    return f"...{html[start:end]}..."


class TestGarminLinkErrorRecovery:
    """Test that Garmin link errors allow immediate retry without refresh.

    Bug: Error responses only return error message div, not form
    Expected: Error responses should include both error message AND form for retry
    """

    def test_link_failure_includes_form_for_retry(self, client: TestClient, test_user_token: str):
        """Failed link attempt should return error + form (not just error)."""
        with patch("app.routes.garmin.GarminService") as mock_service_class:
            # Mock link_account to return False (invalid credentials)
            mock_service = AsyncMock()
            mock_service.link_account.return_value = False
            mock_service_class.return_value = mock_service

            response = client.post(
                "/garmin/link",
                data={
                    "username": INVALID_GARMIN_USERNAME,
                    "password": INVALID_GARMIN_PASSWORD,
                },
                headers={
                    "Authorization": f"Bearer {test_user_token}",
                    "HX-Request": "true",
                },
            )

        assert response.status_code == 400
        html = response.text

        # Should contain error message
        assert "Failed to link Garmin account" in html
        assert 'data-testid="error-message"' in html

        # BUG: Current code only returns error div, not form
        # This test will FAIL until we fix it
        assert 'data-testid="form-link-garmin"' in html, (
            "Error response must include form for immediate retry. "
            "Users should not need to refresh page to retry after error. "
            f"Current response only contains: {html[:300]}"
        )

        # Form must have both input fields for retry
        required_fields = ['name="username"', 'name="password"']
        assert all(field in html for field in required_fields), (
            f"Form must have {', '.join(required_fields)} for retry"
        )

    def test_link_exception_includes_form_for_retry(self, client: TestClient, test_user_token: str):
        """Unexpected exceptions should also return error + form (not just error)."""
        with patch("app.routes.garmin.GarminService") as mock_service_class:
            # Mock service to raise exception
            mock_service = AsyncMock()
            mock_service.link_account.side_effect = Exception("Network timeout")
            mock_service_class.return_value = mock_service

            response = client.post(
                "/garmin/link",
                data={
                    "username": TEST_GARMIN_USERNAME,
                    "password": TEST_GARMIN_PASSWORD,
                },
                headers={
                    "Authorization": f"Bearer {test_user_token}",
                    "HX-Request": "true",
                },
            )

        assert response.status_code == 500
        html = response.text

        # Should contain generic error message (no internal details)
        assert "Something went wrong" in html
        assert 'data-testid="error-message"' in html
        assert "Network timeout" not in html  # Internal error not exposed

        # BUG: Current code only returns error div, not form
        # This test will FAIL until we fix it
        assert 'data-testid="form-link-garmin"' in html, (
            "Exception response must include form for immediate retry. "
            "Users should not need to refresh page to retry after server error. "
            f"Current response only contains: {html[:300]}"
        )

        # Form must have both input fields for retry
        required_fields = ['name="username"', 'name="password"']
        assert all(field in html for field in required_fields), (
            f"Form must have {', '.join(required_fields)} for retry"
        )
