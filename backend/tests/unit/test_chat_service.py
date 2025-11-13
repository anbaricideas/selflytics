"""Tests for ChatService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService


class TestChatService:
    """Test ChatService orchestration."""

    @pytest.mark.asyncio
    async def test_send_message_new_conversation(self):
        """Test sending message that creates new conversation."""
        request = ChatRequest(message="How am I doing?")

        # Mock conversation service
        mock_conversation = MagicMock()
        mock_conversation.conversation_id = "conv-123"
        mock_conversation.user_id = "user-456"

        mock_user_message = MagicMock()
        mock_user_message.message_id = "msg-1"

        # Mock agent response
        mock_agent_result = MagicMock()
        mock_agent_result.data = ChatResponse(
            message="You're doing great! 5 runs this week.",
            data_sources_used=["activities"],
            confidence=0.9,
            suggested_followup="What was your average pace?",
        )
        mock_agent_result.usage.return_value = {
            "prompt_tokens": 500,
            "completion_tokens": 300,
        }

        with (
            patch("app.services.chat_service.ConversationService") as mock_conv_service_class,
            patch("app.services.chat_service.create_chat_agent") as mock_create_agent,
        ):
            # Setup conversation service mock
            mock_conv_service = AsyncMock()
            mock_conv_service.create_conversation.return_value = mock_conversation
            mock_conv_service.add_message.side_effect = [
                mock_user_message,
                MagicMock(),
            ]  # User msg, then assistant msg
            mock_conv_service.get_message_history.return_value = [mock_user_message]
            mock_conv_service_class.return_value = mock_conv_service

            # Setup agent mock
            mock_agent = AsyncMock()
            mock_agent.run.return_value = mock_agent_result
            mock_create_agent.return_value = mock_agent

            # Execute
            service = ChatService()
            response, conversation_id = await service.send_message(
                user_id="user-456", request=request
            )

            # Verify conversation created
            mock_conv_service.create_conversation.assert_called_once_with(user_id="user-456")

            # Verify user message saved
            assert mock_conv_service.add_message.call_count == 2  # User + assistant

            # Verify agent was called
            mock_agent.run.assert_called_once()
            call_args = mock_agent.run.call_args
            assert call_args[0][0] == "How am I doing?"
            assert call_args[1]["deps"] == "user-456"

            # Verify response
            assert response.message == "You're doing great! 5 runs this week."
            assert response.confidence == 0.9
            assert conversation_id == "conv-123"

    @pytest.mark.asyncio
    async def test_send_message_existing_conversation(self):
        """Test sending message to existing conversation."""
        request = ChatRequest(message="What about last month?", conversation_id="conv-123")

        # Mock existing conversation
        mock_conversation = MagicMock()
        mock_conversation.conversation_id = "conv-123"
        mock_conversation.user_id = "user-456"

        # Mock message history
        mock_history = [
            MagicMock(role="user", content="How am I doing?", timestamp=datetime.now(UTC)),
            MagicMock(role="assistant", content="You're doing great!", timestamp=datetime.now(UTC)),
        ]

        # Mock agent response
        mock_agent_result = MagicMock()
        mock_agent_result.data = ChatResponse(
            message="Last month you had 8 runs.", data_sources_used=["activities"], confidence=0.85
        )
        mock_agent_result.usage.return_value = {
            "prompt_tokens": 800,
            "completion_tokens": 200,
        }

        with (
            patch("app.services.chat_service.ConversationService") as mock_conv_service_class,
            patch("app.services.chat_service.create_chat_agent") as mock_create_agent,
        ):
            mock_conv_service = AsyncMock()
            mock_conv_service.get_conversation.return_value = mock_conversation
            mock_conv_service.add_message.return_value = MagicMock()
            mock_conv_service.get_message_history.return_value = [*mock_history, MagicMock()]
            mock_conv_service_class.return_value = mock_conv_service

            mock_agent = AsyncMock()
            mock_agent.run.return_value = mock_agent_result
            mock_create_agent.return_value = mock_agent

            # Execute
            service = ChatService()
            response, conversation_id = await service.send_message(
                user_id="user-456", request=request
            )

            # Verify conversation retrieved
            mock_conv_service.get_conversation.assert_called_once_with("conv-123")

            # Verify conversation NOT created
            mock_conv_service.create_conversation.assert_not_called()

            # Verify message history was passed to agent
            mock_agent.run.assert_called_once()
            call_args = mock_agent.run.call_args
            assert "message_history" in call_args[1]

            assert response.message == "Last month you had 8 runs."
            assert conversation_id == "conv-123"

    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found(self):
        """Test error when conversation doesn't exist."""
        request = ChatRequest(message="Test", conversation_id="nonexistent")

        with patch("app.services.chat_service.ConversationService") as mock_conv_service_class:
            mock_conv_service = AsyncMock()
            mock_conv_service.get_conversation.return_value = None
            mock_conv_service_class.return_value = mock_conv_service

            service = ChatService()

            with pytest.raises(ValueError, match="Conversation not found"):
                await service.send_message(user_id="user-456", request=request)

    @pytest.mark.asyncio
    async def test_send_message_generates_title_for_first_exchange(self):
        """Test that title is generated for first message."""
        request = ChatRequest(message="How many runs did I do?")

        mock_conversation = MagicMock()
        mock_conversation.conversation_id = "conv-123"

        mock_agent_result = MagicMock()
        mock_agent_result.data = ChatResponse(
            message="You did 5 runs.", data_sources_used=[], confidence=0.9
        )
        mock_agent_result.usage.return_value = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        }

        with (
            patch("app.services.chat_service.ConversationService") as mock_conv_service_class,
            patch("app.services.chat_service.create_chat_agent") as mock_create_agent,
        ):
            mock_conv_service = AsyncMock()
            mock_conv_service.create_conversation.return_value = mock_conversation
            mock_conv_service.add_message.return_value = MagicMock()
            # Only 1 message in history (the one we just added)
            mock_conv_service.get_message_history.return_value = [MagicMock()]
            mock_conv_service_class.return_value = mock_conv_service

            mock_agent = AsyncMock()
            mock_agent.run.return_value = mock_agent_result
            mock_create_agent.return_value = mock_agent

            service = ChatService()
            await service.send_message(user_id="user-456", request=request)

            # Verify title generation was called
            mock_conv_service.generate_title.assert_called_once_with(
                conversation_id="conv-123", first_user_message="How many runs did I do?"
            )

    @pytest.mark.asyncio
    async def test_send_message_includes_cost_in_metadata(self):
        """Test that message metadata includes cost tracking."""
        request = ChatRequest(message="Test")

        mock_conversation = MagicMock()
        mock_conversation.conversation_id = "conv-123"

        mock_agent_result = MagicMock()
        mock_agent_result.data = ChatResponse(
            message="Response", data_sources_used=[], confidence=0.8
        )
        mock_agent_result.usage.return_value = {
            "prompt_tokens": 500,
            "completion_tokens": 300,
        }

        with (
            patch("app.services.chat_service.ConversationService") as mock_conv_service_class,
            patch("app.services.chat_service.create_chat_agent") as mock_create_agent,
        ):
            mock_conv_service = AsyncMock()
            mock_conv_service.create_conversation.return_value = mock_conversation
            mock_conv_service.get_message_history.return_value = [MagicMock()]

            # Track add_message calls
            add_message_calls = []

            async def track_add_message(*args, **kwargs):
                add_message_calls.append(kwargs)
                return MagicMock()

            mock_conv_service.add_message.side_effect = track_add_message
            mock_conv_service_class.return_value = mock_conv_service

            mock_agent = AsyncMock()
            mock_agent.run.return_value = mock_agent_result
            mock_create_agent.return_value = mock_agent

            service = ChatService()
            await service.send_message(user_id="user-456", request=request)

            # Verify assistant message includes cost in metadata
            assistant_message_call = add_message_calls[1]  # Second call is assistant
            assert "metadata" in assistant_message_call
            metadata = assistant_message_call["metadata"]
            assert "cost_usd" in metadata
            assert "tokens" in metadata
            assert "confidence" in metadata
            assert metadata["confidence"] == 0.8
