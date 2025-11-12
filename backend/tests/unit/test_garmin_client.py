"""Unit tests for GarminClient service."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.garmin_data import DailyMetrics, HealthSnapshot
from app.services.garmin_client import GarminClient


@pytest.fixture
def mock_firestore():
    """Mock Firestore client."""
    with patch("app.services.garmin_client.get_firestore_client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_garth():
    """Mock garth library."""
    with patch("app.services.garmin_client.garth") as mock:
        yield mock


@pytest.fixture
def mock_encryption():
    """Mock encryption functions."""
    with (
        patch("app.services.garmin_client.encrypt_token") as mock_encrypt,
        patch("app.services.garmin_client.decrypt_token") as mock_decrypt,
    ):
        # Default behavior: return simple encrypted/decrypted values
        mock_encrypt.side_effect = lambda x: f"encrypted_{x}"
        mock_decrypt.side_effect = lambda x: {"token": x}
        yield mock_encrypt, mock_decrypt


@pytest.fixture
def garmin_client(mock_firestore):
    """Create GarminClient instance with mocked dependencies."""
    return GarminClient(user_id="test_user_123")


def setup_firestore_with_tokens(mock_firestore):
    """Helper function to setup Firestore mock with tokens."""
    mock_doc = MagicMock()
    mock_doc.exists = True
    now = datetime.utcnow()
    token_data = {
        "user_id": "test_user_123",
        "oauth1_token_encrypted": "encrypted_oauth1",
        "oauth2_token_encrypted": "encrypted_oauth2",
        "token_expiry": None,
        "last_sync": now,
        "mfa_enabled": False,
        "created_at": now,
        "updated_at": now,
    }
    mock_doc.to_dict = MagicMock(return_value=token_data)
    mock_document = MagicMock()
    mock_document.get = MagicMock(return_value=mock_doc)
    mock_collection = MagicMock()
    mock_collection.document = MagicMock(return_value=mock_document)
    mock_firestore.collection = MagicMock(return_value=mock_collection)
    return mock_firestore


class TestGarminClientAuthenticate:
    """Tests for authenticate method."""

    async def test_authenticate_success(self, garmin_client, mock_garth, mock_encryption):
        """Test successful authentication."""
        # Setup
        mock_garth.login.return_value = None  # Success
        mock_garth.client.oauth1_token = {"token": "oauth1"}
        mock_garth.client.oauth2_token = {"token": "oauth2"}

        # Execute
        result = await garmin_client.authenticate("user@example.com", "password123")

        # Assert
        assert result is True
        mock_garth.login.assert_called_once_with("user@example.com", "password123")

    async def test_authenticate_invalid_credentials(self, garmin_client, mock_garth):
        """Test authentication with invalid credentials."""
        # Setup
        mock_garth.login.side_effect = Exception("Invalid credentials")

        # Execute
        result = await garmin_client.authenticate("user@example.com", "wrong_password")

        # Assert
        assert result is False

    async def test_authenticate_network_error(self, garmin_client, mock_garth):
        """Test authentication with network error."""
        # Setup
        mock_garth.login.side_effect = ConnectionError("Network unavailable")

        # Execute
        result = await garmin_client.authenticate("user@example.com", "password123")

        # Assert
        assert result is False

    async def test_authenticate_persists_tokens_for_reuse(
        self, mock_garth, mock_firestore, mock_encryption
    ):
        """Test that authentication allows token reuse in new client instance."""
        # Setup
        mock_garth.login.return_value = None
        mock_garth.client.oauth1_token = {"token": "oauth1"}
        mock_garth.client.oauth2_token = {"token": "oauth2"}

        # Setup Firestore to persist and return tokens
        saved_data = {}

        def mock_set(data):
            saved_data.update(data)

        def mock_get():
            mock_doc = MagicMock()
            if saved_data:
                mock_doc.exists = True
                mock_doc.to_dict.return_value = saved_data
            else:
                mock_doc.exists = False
            return mock_doc

        mock_collection = MagicMock()
        mock_collection.document().set.side_effect = mock_set
        mock_collection.document().get.side_effect = mock_get
        mock_firestore.collection.return_value = mock_collection

        # Authenticate with first client
        client1 = GarminClient(user_id="test_user_123")
        auth_result = await client1.authenticate("user@example.com", "password123")
        assert auth_result is True

        # Create new client for same user
        client2 = GarminClient(user_id="test_user_123")

        # Should be able to load tokens without re-authenticating
        load_result = await client2.load_tokens()
        assert load_result is True


class TestGarminClientLoadTokens:
    """Tests for load_tokens method."""

    async def test_load_tokens_success(self, mock_firestore, mock_garth, mock_encryption):
        """Test successful token loading from Firestore."""
        # Setup
        _, mock_decrypt = mock_encryption
        mock_decrypt.side_effect = [
            {"token": "oauth1_decrypted"},
            {"token": "oauth2_decrypted"},
        ]

        mock_doc = MagicMock()
        mock_doc.exists = True
        now = datetime.utcnow()
        token_data = {
            "user_id": "test_user_123",
            "oauth1_token_encrypted": "encrypted_oauth1",
            "oauth2_token_encrypted": "encrypted_oauth2",
            "token_expiry": None,
            "last_sync": now,
            "mfa_enabled": False,
            "created_at": now,
            "updated_at": now,
        }
        mock_doc.to_dict = MagicMock(return_value=token_data)

        # Setup the mock chain properly
        mock_document = MagicMock()
        mock_document.get = MagicMock(return_value=mock_doc)
        mock_collection = MagicMock()
        mock_collection.document = MagicMock(return_value=mock_document)
        mock_firestore.collection = MagicMock(return_value=mock_collection)

        # Create client after mocks are fully setup
        garmin_client = GarminClient(user_id="test_user_123")

        # Execute
        result = await garmin_client.load_tokens()

        # Assert
        assert result is True
        assert mock_decrypt.call_count == 2
        assert mock_garth.client.oauth1_token == {"token": "oauth1_decrypted"}
        assert mock_garth.client.oauth2_token == {"token": "oauth2_decrypted"}

    async def test_load_tokens_not_found(self, garmin_client, mock_firestore):
        """Test loading tokens when none exist."""
        # Setup
        mock_doc = MagicMock()
        mock_doc.exists = False

        mock_document = MagicMock()
        mock_document.get.return_value = mock_doc
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_document
        mock_firestore.collection.return_value = mock_collection

        # Execute
        result = await garmin_client.load_tokens()

        # Assert
        assert result is False

    async def test_load_tokens_decryption_error(
        self, garmin_client, mock_firestore, mock_encryption
    ):
        """Test token loading when decryption fails."""
        # Setup
        _, mock_decrypt = mock_encryption
        mock_decrypt.side_effect = Exception("Decryption failed")

        mock_doc = MagicMock()
        mock_doc.exists = True
        now = datetime.utcnow()
        mock_doc.to_dict.return_value = {
            "user_id": "test_user_123",
            "oauth1_token_encrypted": "encrypted_oauth1",
            "oauth2_token_encrypted": "encrypted_oauth2",
            "token_expiry": None,
            "last_sync": now,
            "mfa_enabled": False,
            "created_at": now,
            "updated_at": now,
        }

        mock_document = MagicMock()
        mock_document.get.return_value = mock_doc
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_document
        mock_firestore.collection.return_value = mock_collection

        # Execute
        result = await garmin_client.load_tokens()

        # Assert
        assert result is False


class TestGarminClientGetActivities:
    """Tests for get_activities method."""

    async def test_get_activities_success(self, mock_garth, mock_firestore, mock_encryption):
        """Test successful activity fetching."""
        # Setup
        _, mock_decrypt = mock_encryption
        mock_decrypt.side_effect = [{"token": "oauth1"}, {"token": "oauth2"}]
        setup_firestore_with_tokens(mock_firestore)
        garmin_client = GarminClient(user_id="test_user_123")

        start_date = date(2025, 11, 1)
        end_date = date(2025, 11, 3)

        mock_garth.activities.side_effect = [
            [
                {
                    "activityId": 123,
                    "activityName": "Morning Run",
                    "activityType": "running",
                    "startTimeLocal": "2025-11-01T06:00:00",
                    "distance": 5000,
                    "duration": 1800,
                    "averageHR": 150,
                    "calories": 400,
                    "elevationGain": 50,
                }
            ],
            [],  # No activities on 2025-11-02
            [
                {
                    "activityId": 124,
                    "activityName": "Evening Cycle",
                    "activityType": "cycling",
                    "startTimeLocal": "2025-11-03T17:00:00",
                    "distance": 15000,
                    "duration": 3600,
                    "averageHR": 140,
                    "calories": 600,
                    "elevationGain": 100,
                }
            ],
        ]

        # Execute
        activities = await garmin_client.get_activities(start_date, end_date)

        # Assert
        assert len(activities) == 2
        assert activities[0].activity_id == 123
        assert activities[0].activity_name == "Morning Run"
        assert activities[1].activity_id == 124
        assert activities[1].activity_name == "Evening Cycle"

    async def test_get_activities_not_authenticated(self, garmin_client, mock_firestore):
        """Test activity fetching when not authenticated."""
        # Setup - no tokens available
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_document = MagicMock()
        mock_document.get.return_value = mock_doc
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_document
        mock_firestore.collection.return_value = mock_collection

        # Execute & Assert
        with pytest.raises(Exception, match="Not authenticated"):
            await garmin_client.get_activities(date.today(), date.today())

    async def test_get_activities_with_filter(self, mock_garth, mock_firestore, mock_encryption):
        """Test activity fetching with activity type filter."""
        # Setup
        _, mock_decrypt = mock_encryption
        mock_decrypt.side_effect = [{"token": "oauth1"}, {"token": "oauth2"}]
        setup_firestore_with_tokens(mock_firestore)
        garmin_client = GarminClient(user_id="test_user_123")

        start_date = date(2025, 11, 1)
        end_date = date(2025, 11, 1)

        mock_garth.activities.return_value = [
            {
                "activityId": 123,
                "activityName": "Morning Run",
                "activityType": "running",
                "startTimeLocal": "2025-11-01T06:00:00",
            },
            {
                "activityId": 124,
                "activityName": "Lunch Cycle",
                "activityType": "cycling",
                "startTimeLocal": "2025-11-01T12:00:00",
            },
        ]

        # Execute
        activities = await garmin_client.get_activities(
            start_date, end_date, activity_type="running"
        )

        # Assert
        assert len(activities) == 1
        assert activities[0].activity_type == "running"

    async def test_get_activities_api_error(self, mock_garth, mock_firestore, mock_encryption):
        """Test activity fetching when API returns error."""
        # Setup
        _, mock_decrypt = mock_encryption
        mock_decrypt.side_effect = [{"token": "oauth1"}, {"token": "oauth2"}]
        setup_firestore_with_tokens(mock_firestore)
        garmin_client = GarminClient(user_id="test_user_123")

        mock_garth.activities.side_effect = Exception("API error")

        # Execute
        activities = await garmin_client.get_activities(date.today(), date.today())

        # Assert - should return empty list and log warning
        assert len(activities) == 0


class TestGarminClientGetDailyMetrics:
    """Tests for get_daily_metrics method."""

    async def test_get_daily_metrics_success(self, mock_garth, mock_firestore, mock_encryption):
        """Test successful daily metrics fetching."""
        # Setup
        _, mock_decrypt = mock_encryption
        mock_decrypt.side_effect = [{"token": "oauth1"}, {"token": "oauth2"}]
        setup_firestore_with_tokens(mock_firestore)
        garmin_client = GarminClient(user_id="test_user_123")

        target_date = date(2025, 11, 13)

        mock_garth.daily_summary.return_value = {
            "steps": 10500,
            "distanceMeters": 8000,
            "activeCalories": 800,
            "restingHeartRate": 55,
            "maxHeartRate": 170,
            "avgStressLevel": 30,
            "sleepSeconds": 28800,
        }

        # Execute
        metrics = await garmin_client.get_daily_metrics(target_date)

        # Assert
        assert isinstance(metrics, DailyMetrics)
        assert metrics.date == target_date
        assert metrics.steps == 10500
        assert metrics.distance_meters == 8000
        assert metrics.resting_heart_rate == 55

    async def test_get_daily_metrics_not_authenticated(self, garmin_client, mock_firestore):
        """Test metrics fetching when not authenticated."""
        # Setup
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_document = MagicMock()
        mock_document.get.return_value = mock_doc
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_document
        mock_firestore.collection.return_value = mock_collection

        # Execute & Assert
        with pytest.raises(Exception, match="Not authenticated"):
            await garmin_client.get_daily_metrics(date.today())


class TestGarminClientGetHealthSnapshot:
    """Tests for get_health_snapshot method."""

    async def test_get_health_snapshot_success(self, mock_garth, mock_firestore, mock_encryption):
        """Test successful health snapshot fetching."""
        # Setup
        _, mock_decrypt = mock_encryption
        mock_decrypt.side_effect = [{"token": "oauth1"}, {"token": "oauth2"}]
        setup_firestore_with_tokens(mock_firestore)
        garmin_client = GarminClient(user_id="test_user_123")

        mock_garth.health_snapshot.return_value = {
            "heartRate": 65,
            "respirationRate": 16,
            "stressLevel": 25,
            "spo2": 98.5,
        }

        # Execute
        snapshot = await garmin_client.get_health_snapshot()

        # Assert
        assert isinstance(snapshot, HealthSnapshot)
        assert snapshot.heart_rate == 65
        assert snapshot.respiration_rate == 16
        assert snapshot.stress_level == 25
        assert snapshot.spo2 == 98.5

    async def test_get_health_snapshot_not_authenticated(self, garmin_client, mock_firestore):
        """Test health snapshot fetching when not authenticated."""
        # Setup
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_document = MagicMock()
        mock_document.get.return_value = mock_doc
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_document
        mock_firestore.collection.return_value = mock_collection

        # Execute & Assert
        with pytest.raises(Exception, match="Not authenticated"):
            await garmin_client.get_health_snapshot()
