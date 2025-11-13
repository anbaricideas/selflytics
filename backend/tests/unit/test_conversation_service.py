"""Tests for ConversationService."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.conversation_service import ConversationService


class TestConversationService:
    """Test ConversationService methods."""

    @pytest.fixture
    def mock_firestore(self):
        """Create mock Firestore client."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        return mock_db, mock_collection

    @pytest.mark.asyncio
    async def test_create_conversation(self, mock_firestore):
        """Test creating a new conversation."""
        mock_db, mock_collection = mock_firestore

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            conversation = await service.create_conversation(user_id="user-123")

            # Verify conversation created with correct fields
            assert conversation.user_id == "user-123"
            assert conversation.title == "New Conversation"
            assert conversation.message_count == 0
            assert isinstance(conversation.conversation_id, str)
            assert isinstance(conversation.created_at, datetime)

            # Verify Firestore was called
            mock_collection.document.assert_called_once()
            doc_ref = mock_collection.document.return_value
            doc_ref.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_message(self, mock_firestore):
        """Test adding message to conversation."""
        mock_db, mock_collection = mock_firestore

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            message = await service.add_message(
                conversation_id="conv-123",
                role="user",
                content="Test message",
                metadata={"tokens": 10},
            )

            # Verify message fields
            assert message.conversation_id == "conv-123"
            assert message.role == "user"
            assert message.content == "Test message"
            assert message.metadata == {"tokens": 10}
            assert isinstance(message.message_id, str)
            assert isinstance(message.timestamp, datetime)

            # Verify Firestore calls
            assert mock_collection.document.call_count >= 2  # Conv doc + message doc

    @pytest.mark.asyncio
    async def test_get_message_history(self, mock_firestore):
        """Test retrieving message history."""
        mock_db, mock_collection = mock_firestore

        # Mock message documents
        mock_messages = [
            {
                "message_id": "msg-1",
                "conversation_id": "conv-123",
                "role": "user",
                "content": "First",
                "timestamp": datetime.now(UTC),
                "metadata": None,
            },
            {
                "message_id": "msg-2",
                "conversation_id": "conv-123",
                "role": "assistant",
                "content": "Second",
                "timestamp": datetime.now(UTC),
                "metadata": None,
            },
        ]

        mock_docs = []
        for msg_data in mock_messages:
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = msg_data
            mock_docs.append(mock_doc)

        mock_query = MagicMock()
        mock_query.stream.return_value = reversed(mock_docs)  # Firestore returns newest first

        # Set up mock chain
        mock_subcollection = MagicMock()
        mock_subcollection.order_by.return_value.limit.return_value = mock_query
        mock_doc_ref = MagicMock()
        mock_doc_ref.collection.return_value = mock_subcollection
        mock_collection.document.return_value = mock_doc_ref

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            messages = await service.get_message_history(conversation_id="conv-123", limit=10)

            # Verify messages returned in chronological order
            assert len(messages) == 2
            assert messages[0].content == "First"
            assert messages[1].content == "Second"

    @pytest.mark.asyncio
    async def test_get_conversation(self, mock_firestore):
        """Test getting conversation by ID."""
        mock_db, mock_collection = mock_firestore

        # Mock conversation document
        conv_data = {
            "conversation_id": "conv-123",
            "user_id": "user-456",
            "title": "My Chat",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "message_count": 5,
            "metadata": None,
        }

        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = conv_data
        mock_collection.document.return_value.get.return_value = mock_doc

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            conversation = await service.get_conversation("conv-123")

            assert conversation is not None
            assert conversation.conversation_id == "conv-123"
            assert conversation.title == "My Chat"
            assert conversation.message_count == 5

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, mock_firestore):
        """Test getting non-existent conversation."""
        mock_db, mock_collection = mock_firestore

        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_collection.document.return_value.get.return_value = mock_doc

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            conversation = await service.get_conversation("nonexistent")

            assert conversation is None

    @pytest.mark.asyncio
    async def test_list_conversations(self, mock_firestore):
        """Test listing user's conversations."""
        mock_db, mock_collection = mock_firestore

        # Mock conversation documents
        conv_data_list = [
            {
                "conversation_id": "conv-1",
                "user_id": "user-123",
                "title": "Chat 1",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "message_count": 3,
                "metadata": None,
            },
            {
                "conversation_id": "conv-2",
                "user_id": "user-123",
                "title": "Chat 2",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "message_count": 8,
                "metadata": None,
            },
        ]

        mock_docs = []
        for conv_data in conv_data_list:
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = conv_data
            mock_docs.append(mock_doc)

        mock_query = MagicMock()
        mock_query.stream.return_value = mock_docs

        # Set up query chain
        mock_where = MagicMock()
        mock_where.order_by.return_value.limit.return_value = mock_query
        mock_collection.where.return_value = mock_where

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            conversations = await service.list_conversations(user_id="user-123", limit=20)

            assert len(conversations) == 2
            assert conversations[0].title == "Chat 1"
            assert conversations[1].title == "Chat 2"

    @pytest.mark.asyncio
    async def test_generate_title(self, mock_firestore):
        """Test generating conversation title."""
        mock_db, mock_collection = mock_firestore

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            # Test with short message
            await service.generate_title("conv-123", "Short message")

            # Verify update was called
            mock_doc_ref = mock_collection.document.return_value
            mock_doc_ref.update.assert_called()
            call_args = mock_doc_ref.update.call_args[0][0]
            assert call_args["title"] == "Short message"

    @pytest.mark.asyncio
    async def test_generate_title_long_message(self, mock_firestore):
        """Test generating title from long message (truncated)."""
        mock_db, mock_collection = mock_firestore

        with patch("app.services.conversation_service.get_firestore_client", return_value=mock_db):
            service = ConversationService()

            long_message = "a" * 60  # 60 characters
            await service.generate_title("conv-123", long_message)

            mock_doc_ref = mock_collection.document.return_value
            call_args = mock_doc_ref.update.call_args[0][0]
            # Should be truncated to 50 chars + "..."
            assert len(call_args["title"]) == 53
            assert call_args["title"].endswith("...")
