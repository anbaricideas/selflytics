"""Unit tests for User data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.user import User, UserCreate, UserProfile, UserResponse


@pytest.fixture
def valid_user_profile():
    """Provide a valid UserProfile for tests."""
    return UserProfile(display_name="Test User")


class TestUserProfile:
    """Test UserProfile model validation."""

    def test_user_profile_with_valid_data(self):
        """Test that UserProfile accepts valid data."""
        profile = UserProfile(
            display_name="John Doe",
            timezone="Australia/Sydney",
            units="metric",
        )

        assert profile.display_name == "John Doe"
        assert profile.timezone == "Australia/Sydney"
        assert profile.units == "metric"

    def test_user_profile_with_defaults(self):
        """Test that UserProfile uses default values."""
        profile = UserProfile(display_name="Jane Doe")

        assert profile.display_name == "Jane Doe"
        assert profile.timezone == "Australia/Sydney"
        assert profile.units == "metric"

    def test_user_profile_with_imperial_units(self):
        """Test that UserProfile accepts imperial units."""
        profile = UserProfile(
            display_name="John Doe",
            units="imperial",
        )

        assert profile.units == "imperial"

    def test_user_profile_requires_display_name(self):
        """Test that UserProfile requires display_name."""
        with pytest.raises(ValidationError):
            UserProfile()  # Missing display_name

    def test_user_profile_strips_display_name_whitespace(self):
        """Test that UserProfile strips leading/trailing whitespace from display_name."""
        profile = UserProfile(display_name="  John Doe  ")
        assert profile.display_name == "John Doe"

    @pytest.mark.parametrize(
        "invalid_units",
        ["kilometers", "METRIC", "imperial-system", "", "metre"],
    )
    def test_user_profile_rejects_invalid_units(self, invalid_units):
        """Test that UserProfile only accepts 'metric' or 'imperial'."""
        with pytest.raises(ValidationError, match="units"):
            UserProfile(display_name="Test User", units=invalid_units)

    def test_user_profile_accepts_unicode_display_name(self):
        """Test that UserProfile accepts unicode characters in display_name."""
        profile = UserProfile(display_name="José García 李明")
        assert profile.display_name == "José García 李明"


class TestUser:
    """Test User model validation."""

    def test_user_with_valid_data(self, valid_user_profile):
        """Test that User accepts valid complete data."""
        now = datetime.now(UTC)

        user = User(
            user_id="user123",
            email="test@example.com",
            hashed_password="$2b$12$hashedhashed",  # noqa: S106
            created_at=now,
            updated_at=now,
            profile=valid_user_profile,
            garmin_linked=False,
        )

        assert user.user_id == "user123"
        assert user.email == "test@example.com"
        assert user.profile == valid_user_profile
        assert user.garmin_linked is False
        assert user.garmin_link_date is None

    def test_user_with_garmin_linked(self):
        """Test User model with Garmin account linked."""
        now = datetime.now(UTC)
        profile = UserProfile(display_name="Test User")

        user = User(
            user_id="user123",
            email="test@example.com",
            hashed_password="$2b$12$hashedhashed",  # noqa: S106
            created_at=now,
            updated_at=now,
            profile=profile,
            garmin_linked=True,
            garmin_link_date=now,
        )

        assert user.garmin_linked is True
        assert user.garmin_link_date == now

    def test_user_email_validation(self):
        """Test that User validates email format."""
        now = datetime.now(UTC)
        profile = UserProfile(display_name="Test User")

        # Invalid email should raise validation error
        with pytest.raises(ValidationError, match="email"):
            User(
                user_id="user123",
                email="not-an-email",
                hashed_password="$2b$12$hashedhashed",  # noqa: S106
                created_at=now,
                updated_at=now,
                profile=profile,
            )

    def test_user_requires_all_fields(self):
        """Test that User requires all non-optional fields."""
        with pytest.raises(ValidationError):
            User(
                user_id="user123",
                # Missing required fields
            )


class TestUserCreate:
    """Test UserCreate model for registration."""

    def test_user_create_with_valid_data(self):
        """Test that UserCreate accepts valid registration data."""
        user_create = UserCreate(
            email="newuser@example.com",
            password="securepassword123",  # noqa: S106
            display_name="New User",
        )

        assert user_create.email == "newuser@example.com"
        assert user_create.password == "securepassword123"  # noqa: S105
        assert user_create.display_name == "New User"

    def test_user_create_password_min_length(self):
        """Test that UserCreate enforces minimum password length."""
        # Password too short (less than 8 characters)
        with pytest.raises(ValidationError, match="at least 8 characters"):
            UserCreate(
                email="test@example.com",
                password="short",  # noqa: S106
                display_name="Test User",
            )

    def test_user_create_valid_8_char_password(self):
        """Test that UserCreate accepts exactly 8 character password."""
        user_create = UserCreate(
            email="test@example.com",
            password="12345678",  # noqa: S106
            display_name="Test User",
        )

        assert user_create.password == "12345678"  # noqa: S105

    def test_user_create_email_validation(self):
        """Test that UserCreate validates email format."""
        with pytest.raises(ValidationError, match="email"):
            UserCreate(
                email="invalid-email",
                password="securepassword123",  # noqa: S106
                display_name="Test User",
            )

    @pytest.mark.parametrize(
        ("missing_field", "test_data"),
        [
            ("password", {"email": "test@example.com", "display_name": "Test User"}),
            ("email", {"password": "securepassword123", "display_name": "Test User"}),
            ("display_name", {"email": "test@example.com", "password": "securepassword123"}),
        ],
    )
    def test_user_create_requires_all_fields(self, missing_field, test_data):
        """Test that UserCreate requires all fields."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**test_data)

        # Verify the missing field is in the error
        errors = exc_info.value.errors()
        assert any(error["loc"][0] == missing_field for error in errors)

    def test_user_create_strips_email_whitespace(self):
        """Test that UserCreate strips leading/trailing whitespace from email."""
        user_create = UserCreate(
            email="  test@example.com  ",
            password="securepassword123",  # noqa: S106
            display_name="Test User",
        )
        assert user_create.email == "test@example.com"

    def test_user_create_normalizes_email_to_lowercase(self):
        """Test that UserCreate normalizes email to lowercase."""
        user_create = UserCreate(
            email="User@Example.COM",
            password="securepassword123",  # noqa: S106
            display_name="Test User",
        )
        assert user_create.email == "user@example.com"

    def test_user_create_password_max_length(self):
        """Test that UserCreate enforces max password length for bcrypt."""
        # Bcrypt has 72-byte limit - passwords longer than this should be rejected
        with pytest.raises(ValidationError, match="password"):
            UserCreate(
                email="test@example.com",
                password="x" * 73,
                display_name="Test User",
            )

    def test_user_create_strips_display_name_whitespace(self):
        """Test that UserCreate strips whitespace from display_name."""
        user_create = UserCreate(
            email="test@example.com",
            password="securepassword123",  # noqa: S106
            display_name="  John Doe  ",
        )
        assert user_create.display_name == "John Doe"

    @pytest.mark.parametrize(
        "invalid_email",
        [
            "not-an-email",
            "user@@example.com",
            "user@",
            "@example.com",
            "user @example.com",
        ],
    )
    def test_user_create_rejects_invalid_emails(self, invalid_email):
        """Test that UserCreate validates email format strictly."""
        with pytest.raises(ValidationError, match="email"):
            UserCreate(
                email=invalid_email,
                password="securepassword123",  # noqa: S106
                display_name="Test User",
            )


class TestUserResponse:
    """Test UserResponse model for API responses."""

    def test_user_response_with_valid_data(self):
        """Test that UserResponse accepts valid data."""
        profile = UserProfile(display_name="Test User")

        response = UserResponse(
            user_id="user123",
            email="test@example.com",
            profile=profile,
            garmin_linked=False,
        )

        assert response.user_id == "user123"
        assert response.email == "test@example.com"
        assert response.profile == profile
        assert response.garmin_linked is False

    def test_user_response_excludes_password_from_serialization(self, valid_user_profile):
        """Test that UserResponse excludes password when serialized to dict/JSON."""
        response = UserResponse(
            user_id="user123",
            email="test@example.com",
            profile=valid_user_profile,
            garmin_linked=True,
        )

        # Test actual serialization (what goes over the wire)
        response_dict = response.model_dump()
        response_json = response.model_dump_json()

        # Password fields should not be in serialized output
        assert "password" not in response_dict
        assert "hashed_password" not in response_dict
        assert "password" not in response_json
        assert "hashed_password" not in response_json

        # Verify expected fields ARE present
        assert "user_id" in response_dict
        assert "email" in response_dict
        assert "profile" in response_dict
        assert "garmin_linked" in response_dict

    def test_user_response_with_garmin_linked(self):
        """Test UserResponse with Garmin account linked."""
        profile = UserProfile(display_name="Test User")

        response = UserResponse(
            user_id="user123",
            email="test@example.com",
            profile=profile,
            garmin_linked=True,
        )

        assert response.garmin_linked is True
