"""Unit tests for Garmin data models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.models.garmin_data import DailyMetrics, GarminActivity, GarminUserProfile, HealthSnapshot


class TestGarminActivity:
    """Tests for GarminActivity model."""

    def test_garmin_activity_valid_data(self):
        """Test GarminActivity with valid data."""
        activity_data = {
            "activityId": 12345678,
            "activityName": "Morning Run",
            "activityType": "running",
            "startTimeLocal": "2025-01-13T06:30:00",
            "distance": 5000.0,
            "duration": 1800,
            "averageHR": 145,
            "calories": 350,
            "elevationGain": 50.5,
        }

        activity = GarminActivity(**activity_data)

        assert activity.activity_id == 12345678
        assert activity.activity_name == "Morning Run"
        assert activity.activity_type == "running"
        assert activity.distance_meters == 5000.0
        assert activity.duration_seconds == 1800
        assert activity.average_hr == 145
        assert activity.calories == 350
        assert activity.elevation_gain == 50.5

    def test_garmin_activity_optional_fields(self):
        """Test GarminActivity with only required fields."""
        activity_data = {
            "activityId": 12345678,
            "activityName": "Morning Run",
            "activityType": "running",
            "startTimeLocal": "2025-01-13T06:30:00",
        }

        activity = GarminActivity(**activity_data)

        assert activity.activity_id == 12345678
        assert activity.activity_name == "Morning Run"
        assert activity.distance_meters is None
        assert activity.duration_seconds is None
        assert activity.average_hr is None

    def test_garmin_activity_missing_required_field(self):
        """Test GarminActivity validation fails when required field is missing."""
        activity_data = {
            "activityName": "Morning Run",
            "activityType": "running",
            "startTimeLocal": "2025-01-13T06:30:00",
        }

        with pytest.raises(ValidationError) as exc_info:
            GarminActivity(**activity_data)

        # Check that activityId field is mentioned (could be activityid in lowercase)
        error_str = str(exc_info.value).lower()
        assert "activityid" in error_str or "activity_id" in error_str

    def test_garmin_activity_alias_handling(self):
        """Test that field aliases work correctly."""
        # Using camelCase (API response format)
        activity_data = {
            "activityId": 12345678,
            "activityName": "Morning Run",
            "activityType": "running",
            "startTimeLocal": "2025-01-13T06:30:00",
            "averageHR": 145,
        }

        activity = GarminActivity(**activity_data)
        assert activity.average_hr == 145

        # Should also accept snake_case
        activity_data_snake = {
            "activity_id": 12345678,
            "activity_name": "Morning Run",
            "activity_type": "running",
            "start_time_local": "2025-01-13T06:30:00",
            "average_hr": 145,
        }

        activity2 = GarminActivity(**activity_data_snake)
        assert activity2.average_hr == 145


class TestDailyMetrics:
    """Tests for DailyMetrics model."""

    def test_daily_metrics_valid_data(self):
        """Test DailyMetrics with valid data."""
        metrics_data = {
            "date": date(2025, 1, 13),
            "steps": 10500,
            "distance_meters": 8500.0,
            "active_calories": 450,
            "resting_heart_rate": 58,
            "max_heart_rate": 175,
            "avg_stress_level": 35,
            "sleep_seconds": 28800,
        }

        metrics = DailyMetrics(**metrics_data)

        assert metrics.date == date(2025, 1, 13)
        assert metrics.steps == 10500
        assert metrics.distance_meters == 8500.0
        assert metrics.active_calories == 450
        assert metrics.resting_heart_rate == 58
        assert metrics.max_heart_rate == 175
        assert metrics.avg_stress_level == 35
        assert metrics.sleep_seconds == 28800

    def test_daily_metrics_required_date_only(self):
        """Test DailyMetrics with only required date field."""
        metrics_data = {"date": date(2025, 1, 13)}

        metrics = DailyMetrics(**metrics_data)

        assert metrics.date == date(2025, 1, 13)
        assert metrics.steps is None
        assert metrics.distance_meters is None
        assert metrics.resting_heart_rate is None

    def test_daily_metrics_missing_date(self):
        """Test DailyMetrics validation fails without date."""
        metrics_data = {"steps": 10500}

        with pytest.raises(ValidationError) as exc_info:
            DailyMetrics(**metrics_data)

        assert "date" in str(exc_info.value).lower()


class TestHealthSnapshot:
    """Tests for HealthSnapshot model."""

    def test_health_snapshot_valid_data(self):
        """Test HealthSnapshot with valid data."""
        snapshot_data = {
            "timestamp": datetime(2025, 1, 13, 14, 30, 0),
            "heart_rate": 72,
            "respiration_rate": 14,
            "stress_level": 28,
            "spo2": 98.5,
        }

        snapshot = HealthSnapshot(**snapshot_data)

        assert snapshot.timestamp == datetime(2025, 1, 13, 14, 30, 0)
        assert snapshot.heart_rate == 72
        assert snapshot.respiration_rate == 14
        assert snapshot.stress_level == 28
        assert snapshot.spo2 == 98.5

    def test_health_snapshot_required_timestamp_only(self):
        """Test HealthSnapshot with only required timestamp field."""
        snapshot_data = {"timestamp": datetime(2025, 1, 13, 14, 30, 0)}

        snapshot = HealthSnapshot(**snapshot_data)

        assert snapshot.timestamp == datetime(2025, 1, 13, 14, 30, 0)
        assert snapshot.heart_rate is None
        assert snapshot.respiration_rate is None
        assert snapshot.stress_level is None
        assert snapshot.spo2 is None

    def test_health_snapshot_missing_timestamp(self):
        """Test HealthSnapshot validation fails without timestamp."""
        snapshot_data = {"heart_rate": 72}

        with pytest.raises(ValidationError) as exc_info:
            HealthSnapshot(**snapshot_data)

        assert "timestamp" in str(exc_info.value).lower()


class TestGarminUserProfile:
    """Tests for GarminUserProfile model."""

    def test_garmin_user_profile_valid_data(self):
        """Test GarminUserProfile with valid data."""
        profile_data = {
            "user_id": "12345",
            "display_name": "John Doe",
            "email": "john@example.com",
            "profile_image_url": "https://example.com/profile.jpg",
        }

        profile = GarminUserProfile(**profile_data)

        assert profile.user_id == "12345"
        assert profile.display_name == "John Doe"
        assert profile.email == "john@example.com"
        assert profile.profile_image_url == "https://example.com/profile.jpg"

    def test_garmin_user_profile_required_fields_only(self):
        """Test GarminUserProfile with only required fields."""
        profile_data = {
            "user_id": "12345",
            "display_name": "John Doe",
        }

        profile = GarminUserProfile(**profile_data)

        assert profile.user_id == "12345"
        assert profile.display_name == "John Doe"
        assert profile.email is None
        assert profile.profile_image_url is None

    def test_garmin_user_profile_missing_required_field(self):
        """Test GarminUserProfile validation fails without required fields."""
        profile_data = {"email": "john@example.com"}

        with pytest.raises(ValidationError) as exc_info:
            GarminUserProfile(**profile_data)

        error_str = str(exc_info.value).lower()
        assert "user_id" in error_str or "display_name" in error_str
