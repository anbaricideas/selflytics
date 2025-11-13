"""Integration tests for chat routes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.dependencies import get_user_service
from app.main import app
from app.models.chat import ChatResponse
from app.models.user import User, UserProfile
from app.services.user_service import UserService


@pytest.fixture
def test_user():
    """Test user data."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "profile": {"display_name": "Test User"},
    }


@pytest.fixture
def mock_user_service(test_user):
    """Mock UserService for integration tests."""
    mock_service = Mock(spec=UserService)

    # Mock verify_token to return test user
    mock_user = User(
        user_id=test_user["user_id"],
        email=test_user["email"],
        hashed_password="hashed",  # noqa: S106 - Test fixture, not a real password
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        profile=UserProfile(**test_user["profile"]),
    )
    mock_service.verify_token = AsyncMock(return_value=mock_user)

    return mock_service


@pytest.fixture
def client(mock_user_service):
    """Provide TestClient with mocked UserService."""
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_token():
    """Mock JWT token for test user."""
    return "mock-jwt-token"


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
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
