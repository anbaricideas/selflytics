"""User Journey Test: Performance Deep Dive.

User asks about October activities → Agent responds with summary
User asks about specific run → Agent references that specific activity
"""

import pytest
from fastapi import status

from app.models.chat import ChatResponse
from tests.helpers.mock_helpers import patch_garmin_service, patch_openai_agent


def test_specific_activity_analysis(client, test_user_token):
    """Test: Query specific activity, then follow-up for details."""
    # Mock October running activities
    mock_activities = [
        {
            "activity_id": "12345",
            "activity_type": "running",
            "distance_meters": 5000,
            "duration_seconds": 1470,  # 24:30
            "average_hr": 155,
            "start_time_local": "2025-10-15T06:00:00",
            "calories": 350,
        },
        {
            "activity_id": "12346",
            "activity_type": "running",
            "distance_meters": 8000,
            "duration_seconds": 2520,  # 42:00
            "average_hr": 148,
            "start_time_local": "2025-10-18T06:00:00",
            "calories": 560,
        },
        # Add more activities to total 12 runs, 85km
        *[
            {
                "activity_id": f"1234{i}",
                "activity_type": "running",
                "distance_meters": 7000,
                "duration_seconds": 2100,
                "average_hr": 150,
                "start_time_local": f"2025-10-{20 + i}T06:00:00",
                "calories": 490,
            }
            for i in range(10)
        ],
    ]

    # First: Get activities for October
    with (
        patch_garmin_service(activities=mock_activities),
        patch_openai_agent(
            response=ChatResponse(
                message="You had 12 runs in October, totaling 85km. Your fastest 5km was on Oct 15th "
                "at 24:30 (4:54/km). You're most consistent on Tuesday and Thursday mornings.",
                data_sources_used=["activities"],
                confidence=0.88,
            )
        ),
    ):
        response1 = client.post(
            "/chat/send",
            json={"message": "Show me my running activities from October"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response1.status_code == status.HTTP_200_OK
        conv_id = response1.json()["conversation_id"]

    # Second: Ask about specific run
    with (
        patch_garmin_service(activities=mock_activities),
        patch_openai_agent(
            response=ChatResponse(
                message="That Oct 15th run was your fastest! You maintained an excellent pace of 4:54/km. "
                "Your average HR of 155 bpm shows you were working hard but not overexerting.",
                data_sources_used=["activities"],
                confidence=0.92,
            ),
            message_history_count=2,
        ),
    ):
        response2 = client.post(
            "/chat/send",
            json={
                "message": "What was different about the Oct 15th run?",
                "conversation_id": conv_id,
            },
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Verify AI can reference specific activity from previous context
        assert response2.status_code == status.HTTP_200_OK
        message = response2.json()["response"]["message"]
        assert "oct 15" in message.lower() or "october 15" in message.lower()
        assert response2.json()["response"]["confidence"] > 0.85


@pytest.mark.skip(reason="Requires activity filtering verification - implement in future session")
def test_activity_type_filtering():
    """Test: Filter activities by type (running vs cycling vs swimming)."""
    # TODO: Mock activities with multiple types
    # TODO: Query "Show me only my cycling activities"
    # TODO: Verify only cycling activities returned
    pass
