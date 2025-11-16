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


# Shared test constants
TEST_PASSWORD = "TestPassword123!"  # noqa: S105 - Standard password for all test fixtures
TEST_GARMIN_PASSWORD = "password123"  # noqa: S105 - Mock Garmin API password for E2E tests


@pytest.fixture(autouse=True)
def reset_app_state():
    """Ensure dependency_overrides is clean before and after each test.

    This fixture runs automatically for every test to prevent state pollution
    from dependency overrides leaking between tests. It clears overrides both
    before (defensive - in case previous test's fixture teardown didn't complete)
    and after (primary cleanup) each test runs.

    This solves the test isolation issue where running 'pytest tests/unit tests/integration'
    together caused 21 tests to fail, even though all tests pass when run separately.
    """
    # Clear before test (defensive - prevents pollution from previous tests)
    app.dependency_overrides.clear()

    yield

    # Clear after test (primary cleanup)
    app.dependency_overrides.clear()


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
        # Mock JWT verification using patch with explicit start/stop
        patcher = patch("app.auth.dependencies.verify_token")
        mock_verify = patcher.start()
        mock_verify.return_value = TokenData(user_id=user_data["user_id"], email=user_data["email"])

        # Override UserService dependency
        app.dependency_overrides[get_user_service] = lambda: user_service

        test_client = TestClient(app, raise_server_exceptions=False)
        if set_cookie:
            test_client.cookies.set("access_token", "Bearer mock-jwt-token")
        yield test_client

        # Cleanup: stop patch first, then clear overrides
        patcher.stop()
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
    """Provide TestClient without authentication for testing auth flows.

    No dependency overrides are set. The autouse reset_app_state fixture
    handles clearing any existing overrides before this fixture runs.
    """
    return TestClient(app, raise_server_exceptions=False)
    # No cleanup needed - autouse fixture handles it


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
