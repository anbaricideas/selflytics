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
def mock_user_service(test_user):
    """Mock UserService for integration tests."""
    from app.auth.password import hash_password

    mock_service = Mock(spec=UserService)

    # Mock get_user_by_id to return test user
    mock_user = User(
        user_id=test_user["user_id"],
        email=test_user["email"],
        hashed_password=hash_password(test_user["password"]),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        profile=UserProfile(**test_user["profile"]),
        garmin_linked=test_user["garmin_linked"],
    )
    mock_service.get_user_by_id = AsyncMock(return_value=mock_user)

    # Mock authenticate method for login tests
    async def mock_authenticate(email: str, password: str):
        if email == test_user["email"] and password == test_user["password"]:
            return mock_user
        return None

    mock_service.authenticate = mock_authenticate

    return mock_service


@pytest.fixture
def client(mock_user_service, test_user):
    """Provide TestClient with mocked UserService and auth."""
    # Mock JWT verification
    with patch("app.auth.dependencies.verify_token") as mock_verify:
        mock_verify.return_value = TokenData(user_id=test_user["user_id"], email=test_user["email"])

        # Override UserService dependency
        app.dependency_overrides[get_user_service] = lambda: mock_user_service

        test_client = TestClient(app, raise_server_exceptions=False)
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


def get_csrf_token(client, endpoint="/register"):
    """Get CSRF token from a form endpoint.

    Returns tuple of (csrf_token, csrf_cookie) for use in POST requests.
    """
    from bs4 import BeautifulSoup

    response = client.get(endpoint)
    assert response.status_code == 200, (
        f"Failed to get form from {endpoint}: {response.status_code}"
    )

    # Get cookie (library uses fastapi-csrf-token as cookie name)
    csrf_cookie = response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None, "CSRF cookie 'fastapi-csrf-token' not set"

    # Get token from HTML (library uses fastapi-csrf-token as field name)
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input is not None, (
        f"CSRF token field 'fastapi-csrf-token' not found in HTML from {endpoint}"
    )
    csrf_token = csrf_input["value"]

    return csrf_token, csrf_cookie
