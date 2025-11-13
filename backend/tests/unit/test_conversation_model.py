"""Tests for conversation data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.conversation import Conversation, ConversationCreate


class TestConversation:
    """Test Conversation model validation."""

    def test_valid_conversation(self):
        """Test creating valid Conversation."""
        now = datetime.now(UTC)
        conversation = Conversation(
            conversation_id="conv-123",
            user_id="user-456",
            title="My fitness goals",
            created_at=now,
            updated_at=now,
            message_count=5,
            metadata={"topics": ["running", "goals"]},
        )

        assert conversation.conversation_id == "conv-123"
        assert conversation.user_id == "user-456"
        assert conversation.title == "My fitness goals"
        assert conversation.created_at == now
        assert conversation.updated_at == now
        assert conversation.message_count == 5
        assert conversation.metadata == {"topics": ["running", "goals"]}

    def test_conversation_defaults(self):
        """Test Conversation with default values."""
        now = datetime.now(UTC)
        conversation = Conversation(
            conversation_id="conv-123",
            user_id="user-456",
            created_at=now,
            updated_at=now,
        )

        assert conversation.title == "New Conversation"
        assert conversation.message_count == 0
        assert conversation.metadata is None

    def test_conversation_required_fields(self):
        """Test Conversation requires key fields."""
        with pytest.raises(ValidationError):
            Conversation(
                user_id="user-456",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )


class TestConversationCreate:
    """Test ConversationCreate model validation."""

    def test_valid_conversation_create(self):
        """Test creating valid ConversationCreate."""
        create = ConversationCreate(user_id="user-123", first_message="How am I doing?")

        assert create.user_id == "user-123"
        assert create.first_message == "How am I doing?"

    def test_conversation_create_required_fields(self):
        """Test ConversationCreate requires all fields."""
        with pytest.raises(ValidationError):
            ConversationCreate(user_id="user-123")

        with pytest.raises(ValidationError):
            ConversationCreate(first_message="Test")
