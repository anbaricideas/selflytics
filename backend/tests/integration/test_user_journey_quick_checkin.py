"""User Journey Test: Quick Daily Check-In.

User logs in → Clicks "Chat" → Asks: "How am I doing this week?"
Agent responds with activity summary and insights.
"""

import pytest
from fastapi import status

from app.models.chat import ChatResponse
from tests.helpers.mock_helpers import patch_garmin_service, patch_openai_agent


def test_quick_daily_checkin(client, test_user_token):
    """Test: User asks for weekly summary, gets activity analysis."""
    # Mock Garmin API data - 5 runs this week
    mock_activities = [
        {
            "activity_type": "running",
            "distance_meters": 5000,
            "duration_seconds": 1800,
            "start_time_local": "2025-11-11T06:00:00",
            "average_hr": 145,
            "calories": 350,
        },
        {
            "activity_type": "running",
            "distance_meters": 8000,
            "duration_seconds": 2880,
            "start_time_local": "2025-11-12T06:00:00",
            "average_hr": 148,
            "calories": 560,
        },
        {
            "activity_type": "running",
            "distance_meters": 5000,
            "duration_seconds": 1800,
            "start_time_local": "2025-11-13T06:00:00",
            "average_hr": 142,
            "calories": 350,
        },
        {
            "activity_type": "running",
            "distance_meters": 10000,
            "duration_seconds": 3600,
            "start_time_local": "2025-11-14T06:00:00",
            "average_hr": 150,
            "calories": 700,
        },
        {
            "activity_type": "running",
            "distance_meters": 5000,
            "duration_seconds": 1740,
            "start_time_local": "2025-11-15T06:00:00",
            "average_hr": 144,
            "calories": 350,
        },
    ]

    # Mock OpenAI response
    mock_ai_response = ChatResponse(
        message="You ran 5 times this week, totaling 33km. Your average pace was 5:27/km. "
        "That's up 15% from last week! You're building great momentum.",
        data_sources_used=["activities"],
        confidence=0.92,
        suggested_followup="What was your average heart rate?",
    )

    with (
        patch_garmin_service(activities=mock_activities),
        patch_openai_agent(response=mock_ai_response),
    ):
        # User sends message
        response = client.post(
            "/chat/send",
            json={"message": "How am I doing this week?"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify conversation created
        assert "conversation_id" in data
        assert data["conversation_id"] is not None

        # Verify AI response structure
        assert data["response"]["message"] == mock_ai_response.message
        assert data["response"]["confidence"] == 0.92
        assert "activities" in data["response"]["data_sources_used"]
        assert data["response"]["suggested_followup"] == "What was your average heart rate?"

        # Verify response contains key information
        message = data["response"]["message"]
        assert "5 times" in message or "five" in message.lower()
        assert "33" in message or "km" in message


@pytest.mark.skip(reason="Requires Firestore verification - implement in future session")
def test_quick_checkin_conversation_saved():
    """Test: Verify conversation and messages saved to Firestore."""
    # TODO: Verify conversation document created
    # TODO: Verify user message saved
    # TODO: Verify AI message saved with metadata (cost, confidence)
    # TODO: Verify conversation title generated from first message
    pass
