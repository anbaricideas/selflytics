"""Tests for chat data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.chat import ChatRequest, ChatResponse, Message


class TestChatResponse:
    """Test ChatResponse model validation."""

    def test_valid_chat_response(self):
        """Test creating valid ChatResponse."""
        response = ChatResponse(
            message="You ran 5 times this week.",
            data_sources_used=["activities"],
            confidence=0.95,
            suggested_followup="What was your average pace?",
        )

        assert response.message == "You ran 5 times this week."
        assert response.data_sources_used == ["activities"]
        assert response.confidence == 0.95
        assert response.suggested_followup == "What was your average pace?"

    def test_chat_response_defaults(self):
        """Test ChatResponse with default values."""
        response = ChatResponse(message="Test message", confidence=0.8)

        assert response.message == "Test message"
        assert response.data_sources_used == []
        assert response.confidence == 0.8
        assert response.suggested_followup is None

    def test_confidence_range_validation(self):
        """Test confidence must be between 0.0 and 1.0."""
        # Valid confidence values
        ChatResponse(message="Test", confidence=0.0)
        ChatResponse(message="Test", confidence=1.0)
        ChatResponse(message="Test", confidence=0.5)

        # Invalid confidence values
        with pytest.raises(ValidationError):
            ChatResponse(message="Test", confidence=-0.1)

        with pytest.raises(ValidationError):
            ChatResponse(message="Test", confidence=1.1)

    def test_message_required(self):
        """Test message field is required."""
        with pytest.raises(ValidationError):
            ChatResponse(confidence=0.8)


class TestMessage:
    """Test Message model validation."""

    def test_valid_message(self):
        """Test creating valid Message."""
        now = datetime.now(UTC)
        message = Message(
            message_id="msg-123",
            conversation_id="conv-456",
            role="user",
            content="How am I doing?",
            timestamp=now,
            metadata={"tokens": 10},
        )

        assert message.message_id == "msg-123"
        assert message.conversation_id == "conv-456"
        assert message.role == "user"
        assert message.content == "How am I doing?"
        assert message.timestamp == now
        assert message.metadata == {"tokens": 10}

    def test_message_without_metadata(self):
        """Test Message without metadata (optional field)."""
        message = Message(
            message_id="msg-123",
            conversation_id="conv-456",
            role="assistant",
            content="You're doing great!",
            timestamp=datetime.now(UTC),
        )

        assert message.metadata is None

    def test_message_required_fields(self):
        """Test Message requires all non-optional fields."""
        with pytest.raises(ValidationError):
            Message(
                conversation_id="conv-456",
                role="user",
                content="Test",
                timestamp=datetime.now(UTC),
            )


class TestChatRequest:
    """Test ChatRequest model validation."""

    def test_valid_chat_request(self):
        """Test creating valid ChatRequest."""
        request = ChatRequest(message="How many runs this week?", conversation_id="conv-123")

        assert request.message == "How many runs this week?"
        assert request.conversation_id == "conv-123"

    def test_chat_request_without_conversation_id(self):
        """Test ChatRequest without conversation_id (new conversation)."""
        request = ChatRequest(message="Hello")

        assert request.message == "Hello"
        assert request.conversation_id is None

    def test_message_min_length(self):
        """Test message must have at least 1 character."""
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_message_max_length(self):
        """Test message cannot exceed 2000 characters."""
        # Valid: 2000 characters
        ChatRequest(message="a" * 2000)

        # Invalid: 2001 characters
        with pytest.raises(ValidationError):
            ChatRequest(message="a" * 2001)
