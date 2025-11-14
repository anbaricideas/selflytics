"""Shared test fixtures for all test types."""

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_user_service
from app.auth.jwt import TokenData
from app.main import app
from app.models.user import User, UserProfile
from app.services.user_service import UserService


# Set dummy API key for tests that create agents
# This prevents "api_key client option must be set" errors
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing-only")


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
        mock_verify.return_value = TokenData(user_id=test_user["user_id"], email=test_user["email"])

        # Override UserService dependency
        app.dependency_overrides[get_user_service] = lambda: mock_user_service

        test_client = TestClient(app)
        yield test_client

        app.dependency_overrides.clear()


@pytest.fixture
def test_user_token():
    """Mock JWT token for test user."""
    return "mock-jwt-token"


@pytest.fixture
def create_mock_user():
    """Factory fixture for creating mock User instances with custom attributes."""

    def _create(**overrides):
        from app.auth.password import hash_password

        defaults = {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "hashed_password": hash_password("TestPassword123!"),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "profile": UserProfile(display_name="Test User"),
            "garmin_linked": False,
        }
        return User(**{**defaults, **overrides})

    return _create


@pytest.fixture
def unauthenticated_client():
    """Provide TestClient without authentication for testing auth flows."""
    # Clear any existing overrides
    app.dependency_overrides.clear()
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
