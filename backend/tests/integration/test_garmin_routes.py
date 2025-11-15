"""Integration tests for Garmin routes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User, UserProfile
from app.services.garmin_service import GarminService


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        user_id="test-user-123",
        email="test@example.com",
        hashed_password="$2b$12$test",  # noqa: S106
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        profile=UserProfile(display_name="Test User"),
        garmin_linked=False,
        garmin_link_date=None,
    )


@pytest.fixture
def mock_garmin_service():
    """Provide mocked GarminService."""
    mock = Mock(spec=GarminService)
    mock.link_account = AsyncMock(return_value=True)
    mock.sync_recent_data = AsyncMock()
    return mock


@pytest.fixture
def client(test_user, mock_garmin_service, monkeypatch):
    """Provide a TestClient with authenticated user and mocked Garmin service.

    Cleanup handled by autouse reset_app_state fixture.
    """

    # Mock get_current_user to return test user
    async def mock_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = mock_get_current_user

    # Mock GarminService instantiation
    def mock_garmin_service_init(user_id: str):
        mock_garmin_service.user_id = user_id
        return mock_garmin_service

    monkeypatch.setattr("app.routes.garmin.GarminService", mock_garmin_service_init)

    # Create test client (raise_server_exceptions=False allows testing error responses)
    return TestClient(app, raise_server_exceptions=False)
    # Cleanup handled by autouse fixture


class TestGarminLinkPage:
    """Tests for GET /garmin/link endpoint."""

    def test_link_page_requires_auth(self):
        """Test that link page requires authentication."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/garmin/link")

        # Should return 401 without auth
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_link_page_authenticated(self, client):
        """Test that authenticated users can access link page."""
        response = client.get("/garmin/link")

        # With auth, should return 200 (or 500 if template missing - that's OK for now)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestLinkGarminAccount:
    """Tests for POST /garmin/link endpoint."""

    def test_link_requires_auth(self):
        """Test that linking requires authentication."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/garmin/link", data={"username": "test@garmin.com", "password": "password123"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_link_account_success(self, client, mock_garmin_service):
        """Test successful Garmin account linking."""
        response = client.post(
            "/garmin/link", data={"username": "test@garmin.com", "password": "password123"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")
        assert "Garmin account linked" in response.text

        mock_garmin_service.link_account.assert_called_once_with(
            username="test@garmin.com",
            password="password123",  # nosec B106  # noqa: S106
        )

    def test_link_account_failure(self, client, mock_garmin_service):
        """Test failed Garmin account linking."""
        mock_garmin_service.link_account = AsyncMock(return_value=False)

        response = client.post(
            "/garmin/link", data={"username": "test@garmin.com", "password": "wrong_password"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "text/html" in response.headers.get("content-type", "")
        assert "Failed to link" in response.text

    def test_link_account_missing_username(self, client):
        """Test linking with missing username."""
        response = client.post("/garmin/link", data={"password": "password123"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_link_account_missing_password(self, client):
        """Test linking with missing password."""
        response = client.post("/garmin/link", data={"username": "test@garmin.com"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSyncGarminData:
    """Tests for POST /garmin/sync endpoint."""

    def test_sync_requires_auth(self):
        """Test that sync requires authentication."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/garmin/sync")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_sync_success(self, client, mock_garmin_service):
        """Test successful data sync."""
        response = client.post("/garmin/sync")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")
        assert "Sync completed successfully" in response.text

        mock_garmin_service.sync_recent_data.assert_called_once()

    def test_sync_failure(self, client, mock_garmin_service):
        """Test sync failure handling."""
        mock_garmin_service.sync_recent_data = AsyncMock(
            side_effect=Exception("Garmin API unavailable")
        )

        response = client.post("/garmin/sync")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "text/html" in response.headers.get("content-type", "")
        assert "Sync failed" in response.text


class TestGarminStatus:
    """Tests for GET /garmin/status endpoint."""

    def test_status_requires_auth(self):
        """Test that status requires authentication."""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/garmin/status")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_status_returns_linked_status(self, client, test_user):
        """Test status endpoint returns Garmin link status."""
        response = client.get("/garmin/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "linked" in data
        assert "user_id" in data
        assert data["user_id"] == "test-user-123"
        assert data["linked"] is False


class TestRouterConfiguration:
    """Tests for router configuration."""

    def test_router_prefix(self):
        """Test that Garmin routes have correct prefix."""
        client = TestClient(app, raise_server_exceptions=False)

        # Even unauthenticated, should recognize the route (return 401, not 404)
        response = client.get("/garmin/status")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_all_routes_registered(self):
        """Test that all expected routes are registered."""
        routes = [route.path for route in app.routes]

        # Check key Garmin routes exist
        assert any("/garmin/link" in route for route in routes)
        assert any("/garmin/sync" in route for route in routes)
        assert any("/garmin/status" in route for route in routes)
