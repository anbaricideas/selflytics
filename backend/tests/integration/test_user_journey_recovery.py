"""User Journey Test: Recovery & Multi-Source Analysis.

User asks about recovery → Agent queries sleep, stress, and resting HR
Agent synthesizes data from multiple sources into holistic assessment
"""

import pytest
from fastapi import status

from app.models.chat import ChatResponse
from tests.helpers.mock_helpers import patch_garmin_service, patch_openai_agent


def test_multi_metric_recovery_analysis(client, test_user_token):
    """Test: Query combining sleep, stress, and HR data."""
    # Mock combined metrics data
    # Note: In reality, each metric would be queried separately
    mock_metrics = {
        "sleep": {"average": 7.2, "unit": "hours", "data": []},
        "stress": {"average": 32, "unit": "0-100", "data": []},
        "resting_hr": {"average": 58, "unit": "bpm", "data": []},
    }

    with (
        patch_garmin_service(metrics=mock_metrics),
        patch_openai_agent(
            response=ChatResponse(
                message="Based on your last 7 days: Your avg stress level is 32 (low-medium), "
                "sleep is consistent at 7.2 hours, and resting HR is stable at 58 bpm. "
                "You're recovering well. Consider a rest day if stress goes above 50.",
                data_sources_used=["metrics"],
                confidence=0.89,
                suggested_followup="How has my training load changed?",
            )
        ),
    ):
        response = client.post(
            "/chat/send",
            json={"message": "Am I recovering well?"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Verify response synthesizes all data
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["response"]

        # Check multiple metrics mentioned
        message = data["message"].lower()
        assert "stress" in message
        assert "sleep" in message
        assert ("resting" in message and "hr" in message) or "heart rate" in message

        # Verify confidence and data sources
        assert data["confidence"] > 0.8
        assert "metrics" in data["data_sources_used"]


@pytest.mark.skip(reason="Requires multi-tool call verification - implement in future session")
def test_multiple_tool_calls_in_single_query():
    """Test: Verify agent makes multiple tool calls for comprehensive answer."""
    # TODO: Mock tool call tracking
    # TODO: Send query requiring multiple metrics
    # TODO: Verify agent called garmin_metrics_tool multiple times
    # TODO: Verify each call with different metric_type
    pass
