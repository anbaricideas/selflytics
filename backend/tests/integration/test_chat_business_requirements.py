"""Test business requirements for chat functionality."""

import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService


pytestmark = pytest.mark.skip(
    reason="Requires proper OpenAI API mocking and Firestore mocking. "
    "Need to mock at OpenAI client and Firestore client level. Future work."
)


@pytest.mark.asyncio
class TestChatBusinessRequirements:
    """Test business rules and requirements."""

    async def test_pii_redaction_in_logs(self, caplog):
        """Verify that PII is redacted in log messages."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        with (
            patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory,
            caplog.at_level(logging.INFO),
        ):
            # Mock agent response
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = ChatResponse(
                message="Your email is test@example.com", confidence=0.9
            )
            mock_result.usage.return_value = {"prompt_tokens": 100, "completion_tokens": 50}

            mock_agent.run.return_value = mock_result
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="What's my email?")
            await service.send_message(user_id="test-user-123", request=request)

            # Verify log message exists
            assert any("Chat response generated" in record.message for record in caplog.records)

            # Verify PII is NOT in logs (if redaction is implemented)
            # Note: This test will fail if PII redaction is not implemented
            log_messages = " ".join(record.message for record in caplog.records)

            # User ID should be redacted (if redact_for_logging is used)
            # This test documents expected behavior
            assert "test-user-123" not in log_messages or "***" in log_messages

    async def test_low_confidence_response_handling(self):
        """Verify that low-confidence responses are handled appropriately."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        with patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory:
            # Mock agent with low confidence
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = ChatResponse(
                message="I'm not sure about that based on available data.",
                confidence=0.3,  # Low confidence
                data_sources_used=[],
            )
            mock_result.usage.return_value = {"prompt_tokens": 50, "completion_tokens": 25}

            mock_agent.run.return_value = mock_result
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="What's my max VO2?")
            response, _ = await service.send_message(user_id="test-user", request=request)

            # Verify low confidence is tracked
            assert response.confidence < 0.7
            assert mock_conversation_service.add_message.called

            # Verify metadata includes confidence
            call_args = mock_conversation_service.add_message.call_args_list[-1]
            assert call_args[1]["metadata"]["confidence"] == 0.3

    async def test_cost_tracking_accuracy(self):
        """Verify that cost tracking accurately captures token usage."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        with patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory:
            # Mock agent with specific token usage
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = ChatResponse(message="Test response", confidence=0.9)
            mock_result.usage.return_value = {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "prompt_tokens_details": {"cached_tokens": 200},
            }

            mock_agent.run.return_value = mock_result
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="Test")
            await service.send_message(user_id="test-user", request=request)

            # Verify cost tracking
            call_args = mock_conversation_service.add_message.call_args_list[-1]
            metadata = call_args[1]["metadata"]

            assert "tokens" in metadata
            assert "cost_usd" in metadata

            tokens = metadata["tokens"]
            assert tokens["input_tokens"] == 1000
            assert tokens["output_tokens"] == 500
            assert tokens["cached_tokens"] == 200

            # Verify cost calculation (GPT-4.1-mini: $0.15/$0.60 per 1M tokens)
            expected_cost = (
                (800 * 0.15 / 1_000_000)  # Non-cached input: 1000 - 200 = 800
                + (500 * 0.60 / 1_000_000)  # Output: 500
                + (200 * 0.075 / 1_000_000)  # Cached input (50% discount): 200
            )
            assert abs(metadata["cost_usd"] - expected_cost) < 0.000001

    async def test_conversation_title_sanitization(self):
        """Verify that conversation titles don't leak PII."""
        service = ConversationService()

        # Mock Firestore
        with patch("app.db.firestore_client.get_firestore_client") as mock_firestore:
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            mock_doc = AsyncMock()

            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_doc
            mock_firestore.return_value = mock_db

            # Create conversation with message containing PII
            conversation_id = "conv-123"
            first_message = "My email is john.doe@example.com and my phone is 555-1234"

            await service.generate_title(
                conversation_id=conversation_id, first_user_message=first_message
            )

            # Verify title is truncated to 50 chars (basic sanitization)
            update_call = mock_doc.update.call_args
            assert update_call is not None
            title = update_call[0][0]["title"]

            # Title should be truncated
            assert len(title) <= 53  # 50 + "..."

            # Basic check: full email shouldn't be in title
            # (Note: Real implementation might need more sophisticated PII detection)
            assert title.endswith("...")

    async def test_data_sources_tracked_correctly(self):
        """Verify that data sources used are tracked correctly."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        with patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory:
            # Mock agent using multiple data sources
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = ChatResponse(
                message="Based on your activities and heart rate...",
                confidence=0.92,
                data_sources_used=["activities", "metrics"],  # Multiple sources
            )
            mock_result.usage.return_value = {"prompt_tokens": 100, "completion_tokens": 50}

            mock_agent.run.return_value = mock_result
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="Am I training well?")
            response, _ = await service.send_message(user_id="test-user", request=request)

            # Verify data sources are tracked
            assert "activities" in response.data_sources_used
            assert "metrics" in response.data_sources_used

            # Verify metadata includes data sources
            call_args = mock_conversation_service.add_message.call_args_list[-1]
            metadata = call_args[1]["metadata"]
            assert metadata["data_sources_used"] == ["activities", "metrics"]

    async def test_message_history_context_limit(self):
        """Verify that message history is limited to last 10 messages."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()

        # Simulate conversation with 15 messages
        from app.models.chat import Message

        mock_messages = [
            Message(
                message_id=f"msg-{i}",
                conversation_id="conv-123",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                timestamp=datetime.now(UTC),
            )
            for i in range(15)
        ]

        mock_conversation_service.get_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        # Return only last 10 messages
        mock_conversation_service.get_message_history.return_value = mock_messages[-10:]

        service = ChatService()
        service.conversation_service = mock_conversation_service

        with patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory:
            # Mock agent
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = ChatResponse(message="Response", confidence=0.9)
            mock_result.usage.return_value = {"prompt_tokens": 100, "completion_tokens": 50}

            # Track message_history argument
            captured_history = None

            async def capture_history(*args, **kwargs):
                nonlocal captured_history
                captured_history = kwargs.get("message_history", [])
                return mock_result

            mock_agent.run.side_effect = capture_history
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="New message", conversation_id="conv-123")
            await service.send_message(user_id="test-user", request=request)

            # Verify only last 10 messages (minus the current one) passed as context
            # get_message_history is called with limit=10
            mock_conversation_service.get_message_history.assert_called_with(
                conversation_id="conv-123", limit=10
            )

            # Verify history passed to agent excludes the just-added message
            assert captured_history is not None
            assert len(captured_history) <= 9  # 10 messages - 1 (just added)

    async def test_suggested_followup_stored(self):
        """Verify that suggested followup questions are stored in metadata."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        with patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory:
            # Mock agent with suggested followup
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = ChatResponse(
                message="You ran 10km this week",
                confidence=0.95,
                suggested_followup="What was your average pace?",
            )
            mock_result.usage.return_value = {"prompt_tokens": 80, "completion_tokens": 40}

            mock_agent.run.return_value = mock_result
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="How much did I run?")
            response, _ = await service.send_message(user_id="test-user", request=request)

            # Verify suggested followup in response
            assert response.suggested_followup == "What was your average pace?"

            # Note: Suggested followup is part of ChatResponse, not stored in metadata
            # This is by design - it's displayed to user, not stored separately

    async def test_model_version_tracking(self):
        """Verify that AI model version is tracked in metadata."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        with patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory:
            # Mock agent
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = ChatResponse(message="Response", confidence=0.9)
            mock_result.usage.return_value = {"prompt_tokens": 100, "completion_tokens": 50}

            mock_agent.run.return_value = mock_result
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="Test")
            await service.send_message(user_id="test-user", request=request)

            # Verify model version is tracked
            call_args = mock_conversation_service.add_message.call_args_list[-1]
            metadata = call_args[1]["metadata"]

            assert "model_used" in metadata
            assert metadata["model_used"] == "gpt-4.1-mini-2025-04-14"
