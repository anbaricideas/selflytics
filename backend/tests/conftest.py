"""Shared test fixtures for all test types."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_user_service
from app.auth.jwt import TokenData
from app.main import app
from app.models.user import User, UserProfile
from app.services.user_service import UserService


@pytest.fixture
def test_user():
    """Test user data shared across all tests."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "profile": {"display_name": "Test User"},
        "garmin_linked": False,
    }


@pytest.fixture
def mock_user_service(test_user):
    """Mock UserService for integration tests."""
    mock_service = Mock(spec=UserService)

    # Mock get_user_by_id to return test user
    mock_user = User(
        user_id=test_user["user_id"],
        email=test_user["email"],
        hashed_password="hashed",  # noqa: S106 - Test fixture, not a real password
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        profile=UserProfile(**test_user["profile"]),
        garmin_linked=test_user["garmin_linked"],
    )
    mock_service.get_user_by_id = AsyncMock(return_value=mock_user)

    return mock_service


@pytest.fixture
def client(mock_user_service, test_user):
    """Provide TestClient with mocked UserService and auth."""
    # Mock JWT verification
    with patch("app.auth.dependencies.verify_token") as mock_verify:
        mock_verify.return_value = TokenData(
            user_id=test_user["user_id"], email=test_user["email"]
        )

        # Override UserService dependency
        app.dependency_overrides[get_user_service] = lambda: mock_user_service

        test_client = TestClient(app)
        yield test_client

        app.dependency_overrides.clear()


@pytest.fixture
def test_user_token():
    """Mock JWT token for test user."""
    return "mock-jwt-token"
