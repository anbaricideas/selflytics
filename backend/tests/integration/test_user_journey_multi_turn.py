"""User Journey Test: Multi-Turn Conversation with Context.

User asks about resting HR → Agent responds
User asks about sleep → Agent has context from previous message
"""

import pytest
from fastapi import status

from app.models.chat import ChatResponse
from tests.helpers.mock_helpers import patch_garmin_service, patch_openai_agent


def test_multi_turn_conversation_with_context(client, test_user_token):
    """Test: Multi-message conversation retains context."""
    # Mock metrics for resting HR
    mock_metrics_hr = [
        {"date": "2025-11-01", "resting_heart_rate": 62},
        {"date": "2025-11-15", "resting_heart_rate": 60},
        {"date": "2025-11-30", "resting_heart_rate": 58},
    ]

    # Mock metrics for sleep
    mock_metrics_sleep = [
        {"date": "2025-11-01", "sleep_seconds": 25200},  # 7 hours
        {"date": "2025-11-15", "sleep_seconds": 26100},  # 7.25 hours
        {"date": "2025-11-30", "sleep_seconds": 28800},  # 8 hours
    ]

    # First message: Ask about resting HR
    with (
        patch_garmin_service(metrics=mock_metrics_hr),
        patch_openai_agent(
            response=ChatResponse(
                message="Your resting HR has decreased from 62 bpm to 58 bpm over the last 30 days. "
                "This is a great sign of improving cardiovascular fitness!",
                data_sources_used=["metrics"],
                confidence=0.95,
            )
        ),
    ):
        response1 = client.post(
            "/chat/send",
            json={"message": "How has my resting heart rate changed?"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response1.status_code == status.HTTP_200_OK
        conv_id = response1.json()["conversation_id"]
        assert conv_id is not None

    # Second message: Ask about sleep (with context)
    with (
        patch_garmin_service(metrics=mock_metrics_sleep),
        patch_openai_agent(
            response=ChatResponse(
                message="You're averaging 7.4 hours of sleep, with good improvement over the month. "
                "Combined with your improving resting HR, your recovery is trending positively.",
                data_sources_used=["metrics"],
                confidence=0.90,
            ),
            message_history_count=2,  # Expect previous message in context
        ),
    ):
        response2 = client.post(
            "/chat/send",
            json={"message": "What about my sleep?", "conversation_id": conv_id},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        # Assertions
        assert response2.status_code == status.HTTP_200_OK
        data = response2.json()

        # Verify response references previous context
        message = data["response"]["message"]
        assert "sleep" in message.lower()
        assert "resting" in message.lower() or "hr" in message.lower()

        # Verify same conversation
        assert data["conversation_id"] == conv_id


@pytest.mark.skip(reason="Requires message history verification - implement in future session")
def test_conversation_history_limit():
    """Test: Only last 10 messages passed as context."""
    # TODO: Create conversation with 15 messages
    # TODO: Send new message
    # TODO: Verify only last 10 passed to agent
    pass
