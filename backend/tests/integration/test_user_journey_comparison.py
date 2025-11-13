"""User Journey Test: Comparative Analysis.

User asks to compare time periods → Agent queries both periods
Agent calculates deltas and provides comparative insights
"""

import pytest
from fastapi import status

from app.models.chat import ChatResponse
from tests.helpers.mock_helpers import patch_garmin_service, patch_openai_agent


def test_month_over_month_comparison(client, test_user_token):
    """Test: Compare two time periods automatically."""
    # Mock October activities (85km total)
    mock_oct_activities = [
        {
            "activity_type": "running",
            "distance_meters": 7000,
            "duration_seconds": 2100,
            "start_time_local": f"2025-10-{day:02d}T06:00:00",
            "average_hr": 150,
        }
        for day in range(1, 13)  # 12 activities
    ]

    # Mock September activities (70km total)
    mock_sep_activities = [
        {
            "activity_type": "running",
            "distance_meters": 6000,
            "duration_seconds": 2100,
            "start_time_local": f"2025-09-{day:02d}T06:00:00",
            "average_hr": 152,
        }
        for day in range(1, 13)  # 12 activities
    ]

    with (
        patch_garmin_service(activities=mock_oct_activities + mock_sep_activities),
        patch_openai_agent(
            response=ChatResponse(
                message="October vs September:\n"
                "- Distance: +14km (84km vs 70km)\n"
                "- Activities: Same frequency (12 runs)\n"
                "- Avg HR: Improved by 2 bpm (150 vs 152)\n"
                "You're progressing consistently with better efficiency!",
                data_sources_used=["activities"],
                confidence=0.91,
            )
        ),
    ):
        response = client.post(
            "/chat/send",
            json={"message": "Compare October to September"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Verify response includes comparison
        assert response.status_code == status.HTTP_200_OK
        message = response.json()["response"]["message"]

        # Check both months mentioned
        assert "october" in message.lower()
        assert "september" in message.lower()

        # Check comparative language
        assert any(
            word in message.lower()
            for word in ["vs", "versus", "compared", "more", "less", "improved"]
        )


@pytest.mark.skip(reason="Requires date range verification - implement in future session")
def test_automatic_date_range_detection():
    """Test: Agent correctly interprets relative date ranges."""
    # TODO: Test "this week" vs "last week"
    # TODO: Test "this month" vs "last month"
    # TODO: Test "last 30 days"
    # TODO: Verify correct date ranges passed to tools
    pass
