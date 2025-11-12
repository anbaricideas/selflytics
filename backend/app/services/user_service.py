"""User service for CRUD operations on user data."""

import uuid
from datetime import UTC, datetime

from app.auth.password import hash_password
from app.db.firestore_client import get_firestore_client
from app.models.user import User, UserCreate, UserProfile


class UserService:
    """Service for managing user data in Firestore."""

    def __init__(self):
        """Initialize UserService with Firestore client."""
        self.db = get_firestore_client()
        self.collection = self.db.collection("users")

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user in Firestore.

        Args:
            user_data: User registration data

        Returns:
            Created User instance with generated ID and timestamps

        Note:
            - Generates a unique user_id (UUID4)
            - Hashes the password using bcrypt
            - Sets created_at and updated_at to current UTC time
            - Stores complete user document in Firestore 'users' collection
        """
        user_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Create user instance
        user = User(
            user_id=user_id,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            created_at=now,
            updated_at=now,
            profile=UserProfile(
                display_name=user_data.display_name,
                timezone="Australia/Sydney",
                units="metric",
            ),
            garmin_linked=False,
            garmin_link_date=None,
        )

        # Save to Firestore
        self.collection.document(user_id).set(user.model_dump())

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: User's email address

        Returns:
            User instance if found, None otherwise

        Note:
            Queries Firestore 'users' collection with email filter
        """
        query = self.collection.where("email", "==", email).limit(1)
        results = query.stream()

        for doc in results:
            return User(**doc.to_dict())

        return None

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by user ID.

        Args:
            user_id: Unique user identifier

        Returns:
            User instance if found, None otherwise

        Note:
            Retrieves document directly from Firestore by document ID
        """
        doc = self.collection.document(user_id).get()

        if doc.exists:
            return User(**doc.to_dict())

        return None
