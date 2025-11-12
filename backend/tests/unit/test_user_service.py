"""Unit tests for UserService."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.models.user import UserCreate
from app.services.user_service import UserService


@pytest.fixture
def mock_firestore_db():
    """Provide a mocked Firestore database client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_db.collection.return_value = mock_collection
    return mock_db, mock_collection


@pytest.fixture
def user_service(mock_firestore_db, monkeypatch):
    """Provide a UserService instance with mocked Firestore."""
    mock_db, _mock_collection = mock_firestore_db

    # Mock get_firestore_client to return our mock
    monkeypatch.setattr("app.services.user_service.get_firestore_client", lambda: mock_db)

    return UserService()


class TestUserServiceCreate:
    """Test UserService.create_user method."""

    async def test_create_user_with_valid_data(self, user_service, mock_firestore_db):
        """Test creating a user with valid registration data."""
        _, mock_collection = mock_firestore_db

        user_data = UserCreate(
            email="newuser@example.com",
            password="securepassword123",  # noqa: S106
            display_name="New User",
        )

        # Mock Firestore document operations
        mock_doc_ref = Mock()
        mock_collection.document.return_value = mock_doc_ref

        user = await user_service.create_user(user_data)

        # Verify user was created with correct data
        assert user.email == "newuser@example.com"
        assert user.profile.display_name == "New User"
        assert user.garmin_linked is False
        assert user.garmin_link_date is None

        # Verify user_id was generated
        assert user.user_id is not None
        assert len(user.user_id) > 0

        # Verify password was hashed (not plain text)
        assert user.hashed_password != "securepassword123"  # noqa: S105
        assert user.hashed_password.startswith("$2b$")

        # Verify timestamps were set
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at == user.updated_at

        # Verify Firestore operations were called
        mock_collection.document.assert_called_once_with(user.user_id)
        mock_doc_ref.set.assert_called_once()

    async def test_create_user_generates_unique_user_id(self, user_service, mock_firestore_db):
        """Test that each created user gets a unique user_id."""
        _, mock_collection = mock_firestore_db

        user_data1 = UserCreate(
            email="user1@example.com",
            password="password123",  # noqa: S106
            display_name="User One",
        )
        user_data2 = UserCreate(
            email="user2@example.com",
            password="password456",  # noqa: S106
            display_name="User Two",
        )

        mock_doc_ref = Mock()
        mock_collection.document.return_value = mock_doc_ref

        user1 = await user_service.create_user(user_data1)
        user2 = await user_service.create_user(user_data2)

        # Users should have different IDs
        assert user1.user_id != user2.user_id

    async def test_create_user_sets_utc_timestamps(self, user_service, mock_firestore_db):
        """Test that created_at and updated_at use UTC timezone."""
        _, mock_collection = mock_firestore_db

        user_data = UserCreate(
            email="test@example.com",
            password="password123",  # noqa: S106
            display_name="Test User",
        )

        mock_doc_ref = Mock()
        mock_collection.document.return_value = mock_doc_ref

        before = datetime.now(UTC)
        user = await user_service.create_user(user_data)
        after = datetime.now(UTC)

        # Verify timestamps are in UTC and within expected range
        assert before <= user.created_at <= after
        assert before <= user.updated_at <= after


class TestUserServiceGetByEmail:
    """Test UserService.get_user_by_email method."""

    async def test_get_user_by_email_found(self, user_service, mock_firestore_db):
        """Test retrieving an existing user by email."""
        _, mock_collection = mock_firestore_db

        # Mock Firestore query result
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "user_id": "user123",
            "email": "existing@example.com",
            "hashed_password": "$2b$12$hashedhashed",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "profile": {
                "display_name": "Existing User",
                "timezone": "Australia/Sydney",
                "units": "metric",
            },
            "garmin_linked": False,
            "garmin_link_date": None,
        }

        mock_query = Mock()
        mock_query.stream.return_value = iter([mock_doc])
        mock_query.limit.return_value = mock_query
        mock_collection.where.return_value = mock_query

        user = await user_service.get_user_by_email("existing@example.com")

        # Verify user was found and data is correct
        assert user is not None
        assert user.user_id == "user123"
        assert user.email == "existing@example.com"
        assert user.profile.display_name == "Existing User"

        # Verify Firestore query was constructed correctly
        mock_collection.where.assert_called_once_with("email", "==", "existing@example.com")
        mock_query.limit.assert_called_once_with(1)

    async def test_get_user_by_email_not_found(self, user_service, mock_firestore_db):
        """Test retrieving a non-existent user returns None."""
        _, mock_collection = mock_firestore_db

        # Mock empty query result
        mock_query = Mock()
        mock_query.stream.return_value = iter([])
        mock_query.limit.return_value = mock_query
        mock_collection.where.return_value = mock_query

        user = await user_service.get_user_by_email("nonexistent@example.com")

        # Verify None is returned for non-existent user
        assert user is None

    async def test_get_user_by_email_with_garmin_linked(self, user_service, mock_firestore_db):
        """Test retrieving user with Garmin account linked."""
        _, mock_collection = mock_firestore_db

        garmin_link_date = datetime.now(UTC)
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "user_id": "user123",
            "email": "garmin_user@example.com",
            "hashed_password": "$2b$12$hashedhashed",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "profile": {
                "display_name": "Garmin User",
                "timezone": "Australia/Sydney",
                "units": "metric",
            },
            "garmin_linked": True,
            "garmin_link_date": garmin_link_date,
        }

        mock_query = Mock()
        mock_query.stream.return_value = iter([mock_doc])
        mock_query.limit.return_value = mock_query
        mock_collection.where.return_value = mock_query

        user = await user_service.get_user_by_email("garmin_user@example.com")

        assert user is not None
        assert user.garmin_linked is True
        assert user.garmin_link_date == garmin_link_date


class TestUserServiceGetById:
    """Test UserService.get_user_by_id method."""

    async def test_get_user_by_id_found(self, user_service, mock_firestore_db):
        """Test retrieving an existing user by ID."""
        _, mock_collection = mock_firestore_db

        # Mock Firestore document get
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "user_id": "user123",
            "email": "test@example.com",
            "hashed_password": "$2b$12$hashedhashed",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "profile": {
                "display_name": "Test User",
                "timezone": "Australia/Sydney",
                "units": "metric",
            },
            "garmin_linked": False,
            "garmin_link_date": None,
        }

        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_collection.document.return_value = mock_doc_ref

        user = await user_service.get_user_by_id("user123")

        # Verify user was found
        assert user is not None
        assert user.user_id == "user123"
        assert user.email == "test@example.com"

        # Verify Firestore operations
        mock_collection.document.assert_called_once_with("user123")
        mock_doc_ref.get.assert_called_once()

    async def test_get_user_by_id_not_found(self, user_service, mock_firestore_db):
        """Test retrieving a non-existent user by ID returns None."""
        _, mock_collection = mock_firestore_db

        # Mock non-existent document
        mock_doc = Mock()
        mock_doc.exists = False

        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_collection.document.return_value = mock_doc_ref

        user = await user_service.get_user_by_id("nonexistent_id")

        # Verify None is returned
        assert user is None


class TestUserServiceFirestoreIntegration:
    """Test UserService Firestore integration behavior."""

    async def test_create_user_stores_correct_document_structure(
        self, user_service, mock_firestore_db
    ):
        """Test that create_user stores data in correct Firestore structure."""
        _, mock_collection = mock_firestore_db

        user_data = UserCreate(
            email="test@example.com",
            password="password123",  # noqa: S106
            display_name="Test User",
        )

        mock_doc_ref = Mock()
        mock_collection.document.return_value = mock_doc_ref

        await user_service.create_user(user_data)

        # Verify set was called with correct structure
        mock_doc_ref.set.assert_called_once()
        stored_data = mock_doc_ref.set.call_args[0][0]

        # Verify all required fields are present
        assert "user_id" in stored_data
        assert "email" in stored_data
        assert "hashed_password" in stored_data
        assert "created_at" in stored_data
        assert "updated_at" in stored_data
        assert "profile" in stored_data
        assert "garmin_linked" in stored_data

        # Verify profile is nested dictionary
        assert isinstance(stored_data["profile"], dict)
        assert "display_name" in stored_data["profile"]
        assert "timezone" in stored_data["profile"]
        assert "units" in stored_data["profile"]
