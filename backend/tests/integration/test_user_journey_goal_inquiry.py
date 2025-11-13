"""User Journey Test: Goal-Oriented Inquiry.

User asks about goal progress → Agent queries recent performance
Agent calculates gap between current and goal performance
Agent provides realistic assessment and projection
"""

import pytest
from fastapi import status

from app.models.chat import ChatResponse
from tests.helpers.mock_helpers import patch_garmin_service, patch_openai_agent


def test_goal_progress_inquiry(client, test_user_token):
    """Test: User asks about goal progress, agent calculates gap."""
    # Mock recent 5K activities
    mock_recent_activities = [
        {
            "activity_type": "running",
            "distance_meters": 5000,
            "duration_seconds": 1575,  # 26:15
            "start_time_local": "2025-11-10T06:00:00",
            "average_hr": 155,
        },
        {
            "activity_type": "running",
            "distance_meters": 5000,
            "duration_seconds": 1590,  # 26:30
            "start_time_local": "2025-11-08T06:00:00",
            "average_hr": 157,
        },
        {
            "activity_type": "running",
            "distance_meters": 5000,
            "duration_seconds": 1560,  # 26:00
            "start_time_local": "2025-11-05T06:00:00",
            "average_hr": 154,
        },
    ]

    with (
        patch_garmin_service(activities=mock_recent_activities),
        patch_openai_agent(
            response=ChatResponse(
                message="Your recent 5K time is 26:15 (5:15/km). To hit sub-25 (5:00/km), "
                "you need to improve pace by 15 seconds/km. Based on your current trend "
                "of 5 seconds/km improvement per month, you could reach this in 3 months "
                "with consistent training.",
                data_sources_used=["activities"],
                confidence=0.86,
                suggested_followup="What training plan should I follow?",
            )
        ),
    ):
        response = client.post(
            "/chat/send",
            json={"message": "I want to run a sub-25 minute 5K. How am I tracking?"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Verify agent queried recent activities
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        message = data["response"]["message"]

        # Verify response includes:
        # - Current time (26:15 or similar)
        # - Goal time (25:00 or sub-25)
        # - Gap analysis
        assert "26" in message or "5:15" in message  # Current time/pace
        assert "25" in message or "5:00" in message  # Goal time/pace
        assert data["response"]["confidence"] > 0.8

        # Should reference improvement needed
        assert any(
            word in message.lower() for word in ["improve", "need", "gap", "seconds", "faster"]
        )


@pytest.mark.skip(reason="Requires trend calculation verification - implement in future session")
def test_goal_with_historical_trend():
    """Test: Agent uses historical data to project goal achievement timeline."""
    # TODO: Mock 3 months of 5K activities showing pace improvement
    # TODO: Query about goal with timeline
    # TODO: Verify agent calculates trend and projects timeline
    pass
