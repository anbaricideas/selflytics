"""Integration tests for authentication routes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_user_service
from app.main import app
from app.models.user import User, UserProfile
from app.services.user_service import UserService


@pytest.fixture
def mock_user_service():
    """Provide a mocked UserService for integration tests.

    This fixture creates a mock UserService that can be configured in individual
    tests. It's automatically injected via app.dependency_overrides in the client
    fixture.
    """
    return Mock(spec=UserService)


@pytest.fixture
def client(mock_user_service):
    """Provide a TestClient with mocked UserService.

    This fixture uses FastAPI's dependency_overrides to inject the mock
    UserService for all routes, preventing Firestore connection attempts.
    The override is automatically cleaned up after each test.
    """
    # Override the get_user_service dependency
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Clean up override after test
    app.dependency_overrides.clear()


@pytest.fixture
def existing_user():
    """Provide an existing user for tests.

    Note: The hashed_password is bcrypt hash of 'password'
    """
    return User(
        user_id="test-user-123",
        email="existing@example.com",
        hashed_password="$2b$12$5szU7XsAq2Rc9349BclbtuMsJfuT9mu24WFaIMCdSkxDtLCiabjpK",  # noqa: S106
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        profile=UserProfile(display_name="Existing User"),
        garmin_linked=False,
    )


class TestRegisterEndpoint:
    """Test POST /auth/register endpoint."""

    def test_register_success(self, client, mock_user_service, existing_user):
        """Test successful user registration."""
        # Mock service to return created user
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service.create_user = AsyncMock(return_value=existing_user)

        response = client.post(
            "/auth/register",
            data={
                "email": "newuser@example.com",
                "password": "securepass123",
                "display_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "existing@example.com"
        assert data["profile"]["display_name"] == "Existing User"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, mock_user_service, existing_user):
        """Test registration with existing email returns 400."""
        # Mock service to return existing user
        mock_user_service.get_user_by_email = AsyncMock(return_value=existing_user)

        response = client.post(
            "/auth/register",
            data={
                "email": "existing@example.com",
                "password": "password123",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email returns 422."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422
        assert "email" in str(response.json())

    def test_register_password_too_short(self, client):
        """Test registration with short password returns 422."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422
        assert "password" in str(response.json())

    def test_register_missing_fields(self, client):
        """Test registration with missing fields returns 422."""
        # Missing password
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "display_name": "Test User"},
        )
        assert response.status_code == 422

        # Missing email
        response = client.post(
            "/auth/register",
            json={"password": "password123", "display_name": "Test User"},
        )
        assert response.status_code == 422

        # Missing display_name
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    """Test POST /auth/login endpoint."""

    def test_login_success(self, client, mock_user_service, existing_user):
        """Test successful login returns access token."""
        # Mock service to return existing user
        mock_user_service.get_user_by_email = AsyncMock(return_value=existing_user)

        response = client.post(
            "/auth/login",
            data={
                "username": "existing@example.com",  # OAuth2 uses 'username' field
                "password": "password",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"  # noqa: S105
        assert len(data["access_token"]) > 0

    def test_login_invalid_email(self, client, mock_user_service):
        """Test login with non-existent email returns 401."""
        # Mock service to return None (user not found)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_wrong_password(self, client, mock_user_service, existing_user):
        """Test login with wrong password returns 401."""
        # Mock service to return user
        mock_user_service.get_user_by_email = AsyncMock(return_value=existing_user)

        response = client.post(
            "/auth/login",
            data={
                "username": "existing@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials returns 422."""
        # Missing password
        response = client.post("/auth/login", data={"username": "test@example.com"})
        assert response.status_code == 422

        # Missing username
        response = client.post("/auth/login", data={"password": "password123"})
        assert response.status_code == 422


class TestMeEndpoint:
    """Test GET /auth/me endpoint."""

    def test_get_me_with_valid_token(self, client, mock_user_service, existing_user):
        """Test /auth/me with valid token returns user data."""
        # Mock service to return user
        mock_user_service.get_user_by_id = AsyncMock(return_value=existing_user)

        # First login to get a token
        mock_user_service.get_user_by_email = AsyncMock(return_value=existing_user)
        login_response = client.post(
            "/auth/login",
            data={
                "username": "existing@example.com",
                "password": "password",
            },
        )
        token = login_response.json()["access_token"]

        # Use token to access /auth/me
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "existing@example.com"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_me_without_token(self, client):
        """Test /auth/me without token returns 401."""
        response = client.get("/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_get_me_with_invalid_token(self, client):
        """Test /auth/me with invalid token returns 401."""
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == 401

    def test_get_me_with_expired_token(self, client, mock_user_service):
        """Test /auth/me with expired token returns 401."""
        # Create an expired token
        from datetime import timedelta

        from app.auth.jwt import create_access_token

        expired_token = create_access_token(
            data={"sub": "user123", "email": "test@example.com"},
            expires_delta=timedelta(seconds=-1),
        )

        response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

        assert response.status_code == 401

    def test_get_me_user_not_found(self, client, mock_user_service, existing_user):
        """Test /auth/me when user no longer exists returns 401."""
        # Login to get valid token
        mock_user_service.get_user_by_email = AsyncMock(return_value=existing_user)
        login_response = client.post(
            "/auth/login",
            data={
                "username": "existing@example.com",
                "password": "password",
            },
        )
        token = login_response.json()["access_token"]

        # Mock service to return None (user deleted)
        mock_user_service.get_user_by_id = AsyncMock(return_value=None)

        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]


class TestAuthFlowIntegration:
    """Test complete authentication flow."""

    def test_register_login_me_flow(self, client, mock_user_service, existing_user):
        """Test complete flow: register -> login -> access protected route."""
        # Step 1: Register
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)
        mock_user_service.create_user = AsyncMock(return_value=existing_user)

        register_response = client.post(
            "/auth/register",
            data={
                "email": "newuser@example.com",
                "password": "securepass123",
                "display_name": "New User",
            },
        )
        assert register_response.status_code == 201

        # Step 2: Login
        mock_user_service.get_user_by_email = AsyncMock(return_value=existing_user)
        login_response = client.post(
            "/auth/login",
            data={
                "username": "newuser@example.com",
                "password": "password",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Step 3: Access protected route
        mock_user_service.get_user_by_id = AsyncMock(return_value=existing_user)
        me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "existing@example.com"
