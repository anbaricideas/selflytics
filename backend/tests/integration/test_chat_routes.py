"""Integration tests for chat routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from app.models.chat import ChatResponse


def test_send_message_new_conversation(client, test_user_token):
    """Test sending message to create new conversation."""
    # Mock chat service
    mock_response = ChatResponse(
        message="You ran 5 times this week!",
        data_sources_used=["activities"],
        confidence=0.9,
        suggested_followup="What was your average pace?",
    )

    with patch("app.routes.chat.ChatService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.send_message.return_value = (mock_response, "conv-123")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/chat/send",
            json={"message": "How am I doing this week?"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["conversation_id"] == "conv-123"
        assert data["response"]["message"] == "You ran 5 times this week!"
        assert data["response"]["confidence"] == 0.9


def test_send_message_existing_conversation(client, test_user_token):
    """Test sending message to existing conversation."""
    mock_response = ChatResponse(
        message="Last month you had 8 runs.", data_sources_used=["activities"], confidence=0.85
    )

    with patch("app.routes.chat.ChatService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.send_message.return_value = (mock_response, "conv-456")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/chat/send",
            json={"message": "What about last month?", "conversation_id": "conv-456"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["conversation_id"] == "conv-456"
        assert data["response"]["message"] == "Last month you had 8 runs."


def test_send_message_unauthorized(client):
    """Test sending message without authentication."""
    response = client.post("/chat/send", json={"message": "Test"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_send_message_invalid_data(client, test_user_token):
    """Test sending message with invalid data."""
    # Empty message
    response = client.post(
        "/chat/send",
        json={"message": ""},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_conversations(client, test_user_token):
    """Test listing user's conversations."""
    mock_conversations = [
        MagicMock(
            conversation_id="conv-1",
            title="My first chat",
            message_count=5,
            model_dump=lambda: {
                "conversation_id": "conv-1",
                "title": "My first chat",
                "message_count": 5,
            },
        ),
        MagicMock(
            conversation_id="conv-2",
            title="Another chat",
            message_count=3,
            model_dump=lambda: {
                "conversation_id": "conv-2",
                "title": "Another chat",
                "message_count": 3,
            },
        ),
    ]

    with patch("app.routes.chat.ChatService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.conversation_service.list_conversations.return_value = mock_conversations
        mock_service_class.return_value = mock_service

        response = client.get(
            "/chat/conversations", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["conversations"]) == 2
        assert data["conversations"][0]["title"] == "My first chat"


def test_get_conversation(client, test_user_token, test_user):
    """Test getting a specific conversation with messages."""
    mock_conversation = MagicMock(
        conversation_id="conv-123",
        user_id=test_user["user_id"],
        title="Test Chat",
        message_count=2,
        model_dump=lambda: {
            "conversation_id": "conv-123",
            "user_id": test_user["user_id"],
            "title": "Test Chat",
            "message_count": 2,
        },
    )

    mock_messages = [
        MagicMock(
            role="user",
            content="Hello",
            model_dump=lambda: {"role": "user", "content": "Hello"},
        ),
        MagicMock(
            role="assistant",
            content="Hi there!",
            model_dump=lambda: {"role": "assistant", "content": "Hi there!"},
        ),
    ]

    with patch("app.routes.chat.ChatService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.conversation_service.get_conversation.return_value = mock_conversation
        mock_service.conversation_service.get_message_history.return_value = mock_messages
        mock_service_class.return_value = mock_service

        response = client.get(
            "/chat/conv-123", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["conversation"]["conversation_id"] == "conv-123"
        assert len(data["messages"]) == 2


def test_get_conversation_not_found(client, test_user_token):
    """Test getting non-existent conversation."""
    with patch("app.routes.chat.ChatService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.conversation_service.get_conversation.return_value = None
        mock_service_class.return_value = mock_service

        response = client.get(
            "/chat/nonexistent", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_conversation_wrong_user(client, test_user_token):
    """Test getting conversation that belongs to another user."""
    mock_conversation = MagicMock(
        user_id="different-user-id",  # Different from test_user
        model_dump=lambda: {"user_id": "different-user-id"},
    )

    with patch("app.routes.chat.ChatService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.conversation_service.get_conversation.return_value = mock_conversation
        mock_service_class.return_value = mock_service

        response = client.get(
            "/chat/conv-123", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_conversation(client, test_user_token):
    """Test deleting a conversation."""
    response = client.delete(
        "/chat/conv-123", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # For now, just verify it returns success
    # Full implementation would actually delete from Firestore
    # Debug: print response if not OK
    if response.status_code != status.HTTP_200_OK:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
