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
        "password": "TestPassword123!",  # Used by integration tests that do actual login
        "profile": {"display_name": "Test User"},
        "garmin_linked": False,
    }


@pytest.fixture
def create_mock_user_service():
    """Factory fixture for creating mock UserService with different user states."""

    def _create_service(user_data: dict, include_auth: bool = True):
        """Create a mock UserService.

        Args:
            user_data: Dict with user_id, email, password, profile, garmin_linked
            include_auth: Whether to mock authenticate method (default True)
        """
        from app.auth.password import hash_password

        mock_service = Mock(spec=UserService)

        # Mock get_user_by_id to return test user
        mock_user = User(
            user_id=user_data["user_id"],
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            profile=UserProfile(**user_data["profile"]),
            garmin_linked=user_data["garmin_linked"],
        )
        mock_service.get_user_by_id = AsyncMock(return_value=mock_user)

        # Mock authenticate method for login tests
        if include_auth:

            async def mock_authenticate(email: str, password: str):
                if email == user_data["email"] and password == user_data["password"]:
                    return mock_user
                return None

            mock_service.authenticate = mock_authenticate

        return mock_service

    return _create_service


@pytest.fixture
def mock_user_service(create_mock_user_service, test_user):
    """Mock UserService for integration tests."""
    return create_mock_user_service(test_user)


@pytest.fixture
def create_authenticated_client():
    """Factory fixture for creating authenticated test clients."""

    def _create_client(user_service, user_data: dict, set_cookie: bool = False):
        """Create an authenticated TestClient.

        Args:
            user_service: Mock UserService instance
            user_data: Dict with user_id and email for token
            set_cookie: Whether to set access_token cookie (default False)
        """
        # Mock JWT verification
        with patch("app.auth.dependencies.verify_token") as mock_verify:
            mock_verify.return_value = TokenData(
                user_id=user_data["user_id"], email=user_data["email"]
            )

            # Override UserService dependency
            app.dependency_overrides[get_user_service] = lambda: user_service

            test_client = TestClient(app, raise_server_exceptions=False)
            if set_cookie:
                test_client.cookies.set("access_token", "Bearer mock-jwt-token")
            yield test_client

            app.dependency_overrides.clear()

    return _create_client


@pytest.fixture
def client(create_authenticated_client, mock_user_service, test_user):
    """Provide TestClient with mocked UserService and auth."""
    yield from create_authenticated_client(mock_user_service, test_user)


@pytest.fixture
def test_user_token():
    """Mock JWT token for test user."""
    return "mock-jwt-token"


@pytest.fixture
def test_user_email(test_user):
    """Test user's email address."""
    return test_user["email"]


@pytest.fixture
def test_user_linked_garmin():
    """Test user data with linked Garmin account."""
    return {
        "user_id": "test-user-linked-123",
        "email": "linked@example.com",
        "password": "TestPassword123!",
        "profile": {"display_name": "Linked User"},
        "garmin_linked": True,
    }


@pytest.fixture
def mock_user_service_linked_garmin(create_mock_user_service, test_user_linked_garmin):
    """Mock UserService for user with linked Garmin."""
    return create_mock_user_service(test_user_linked_garmin, include_auth=False)


@pytest.fixture
def test_user_linked_garmin_token():
    """Mock JWT token for user with linked Garmin."""
    return "mock-jwt-token-linked"


@pytest.fixture
def client_linked_garmin(
    create_authenticated_client, mock_user_service_linked_garmin, test_user_linked_garmin
):
    """Provide TestClient for user with linked Garmin account."""
    yield from create_authenticated_client(
        mock_user_service_linked_garmin, test_user_linked_garmin, set_cookie=True
    )


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
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_service_override():
    """Fixture for temporarily overriding user service dependency.

    Usage:
        with mock_user_service_override(mock_service):
            response = client.post(...)

    Automatically clears overrides after use.
    """
    from contextlib import contextmanager

    @contextmanager
    def _override(mock_service):
        app.dependency_overrides[get_user_service] = lambda: mock_service
        try:
            yield
        finally:
            app.dependency_overrides.clear()

    return _override


@pytest.fixture
def templates():
    """Provide Jinja2 template environment for unit testing templates directly."""
    from pathlib import Path

    from jinja2 import Environment, FileSystemLoader, select_autoescape

    # Get the templates directory from the app
    template_dir = Path(__file__).parent.parent / "app" / "templates"
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),  # Security: Enable autoescape for HTML
    )
