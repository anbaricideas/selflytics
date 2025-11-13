"""User Journey Test: Returning User Experience.

User logs in days later → Sees conversation history
User clicks previous chat → Loads message history
User continues conversation with context
"""

import pytest
from fastapi import status

from app.models.chat import ChatResponse
from tests.helpers.mock_helpers import (
    create_mock_conversation,
    patch_firestore,
    patch_garmin_service,
    patch_openai_agent,
)


@pytest.mark.skip(
    reason="Requires full Firestore mock implementation - implement in future session"
)
def test_load_existing_conversation(client, test_user_token, test_user):
    """Test: Load previous conversation and continue discussion."""
    # Setup: Create existing conversation with history
    conversation, messages = create_mock_conversation(
        user_id=test_user["user_id"],
        messages=[
            {"role": "user", "content": "How many runs this week?"},
            {
                "role": "assistant",
                "content": "You had 5 runs, totaling 28km. Great consistency!",
            },
        ],
        title="Weekly Running Summary",
    )

    with patch_firestore(conversation=conversation, messages=messages):
        # Load conversation list
        list_response = client.get(
            "/chat/conversations", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert list_response.status_code == status.HTTP_200_OK
        convs = list_response.json()["conversations"]
        assert len(convs) > 0
        assert convs[0]["message_count"] == 2

        # Load specific conversation
        conv_response = client.get(
            f"/chat/{conversation.conversation_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert conv_response.status_code == status.HTTP_200_OK
        conv_data = conv_response.json()
        assert len(conv_data["messages"]) == 2
        assert conv_data["messages"][0]["role"] == "user"

        # Send new message in existing conversation
        mock_new_activities = [
            {
                "activity_type": "running",
                "distance_meters": 6000,
                "start_time_local": "2025-11-14T06:00:00",
            },
            {
                "activity_type": "running",
                "distance_meters": 5000,
                "start_time_local": "2025-11-15T06:00:00",
            },
        ]

        with (
            patch_garmin_service(activities=mock_new_activities),
            patch_openai_agent(
                response=ChatResponse(
                    message="Since we last talked, you've completed 2 more runs (11km). "
                    "You're maintaining great consistency!",
                    data_sources_used=["activities"],
                    confidence=0.87,
                ),
                message_history_count=2,  # Previous user + assistant messages
            ),
        ):
            new_msg_response = client.post(
                "/chat/send",
                json={
                    "message": "Any improvement since we last talked?",
                    "conversation_id": conversation.conversation_id,
                },
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

            assert new_msg_response.status_code == status.HTTP_200_OK
            assert new_msg_response.json()["conversation_id"] == conversation.conversation_id


def test_list_conversations_empty(client, test_user_token):
    """Test: New user with no conversations."""
    with patch_openai_agent():
        response = client.get(
            "/chat/conversations", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # May be empty or have conversations from other tests
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
