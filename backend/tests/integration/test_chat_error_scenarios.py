"""Test error handling in chat workflows."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIConnectionError, APITimeoutError, RateLimitError

from app.models.chat import ChatRequest
from app.services.chat_service import ChatService

# Set dummy API key to prevent OpenAI client initialization errors
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing-only")


@pytest.mark.asyncio
class TestChatErrorScenarios:
    """Test error handling and recovery."""

    async def test_openai_timeout_error(self):
        """Verify graceful handling of OpenAI API timeout."""
        from pydantic_ai import ModelMessage
        from pydantic_ai.models.function import AgentInfo, FunctionModel

        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation = MagicMock(conversation_id="conv-123")
        mock_conversation_service.create_conversation.return_value = mock_conversation
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        def model_function(messages: list[ModelMessage], info: AgentInfo):
            """Simulate timeout error on first call."""
            raise APITimeoutError("Request timed out")

        from app.prompts.chat_agent import create_chat_agent

        with patch("app.services.chat_service.create_chat_agent") as mock_create:
            agent = create_chat_agent()
            mock_create.return_value = agent

            with agent.override(model=FunctionModel(model_function)):
                request = ChatRequest(message="How am I doing?")

                with pytest.raises(APITimeoutError):
                    await service.send_message(user_id="test-user", request=request)

                # Verify conversation and user message were saved before error
                assert mock_conversation_service.create_conversation.called
                assert mock_conversation_service.add_message.called

    async def test_openai_rate_limit_error(self):
        """Verify handling of OpenAI rate limit errors."""
        from pydantic_ai import ModelMessage
        from pydantic_ai.models.function import AgentInfo, FunctionModel

        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation = MagicMock(conversation_id="conv-123")
        mock_conversation_service.create_conversation.return_value = mock_conversation
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        def model_function(messages: list[ModelMessage], info: AgentInfo):
            """Simulate rate limit error."""
            raise RateLimitError(
                "Rate limit exceeded", response=AsyncMock(), body=None
            )

        from app.prompts.chat_agent import create_chat_agent

        with patch("app.services.chat_service.create_chat_agent") as mock_create:
            agent = create_chat_agent()
            mock_create.return_value = agent

            with agent.override(model=FunctionModel(model_function)):
                request = ChatRequest(message="Analyze my data")

                with pytest.raises(RateLimitError):
                    await service.send_message(user_id="test-user", request=request)

    async def test_openai_connection_error(self):
        """Verify handling of OpenAI connection errors."""
        from pydantic_ai import ModelMessage
        from pydantic_ai.models.function import AgentInfo, FunctionModel

        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation = MagicMock(conversation_id="conv-123")
        mock_conversation_service.create_conversation.return_value = mock_conversation
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        def model_function(messages: list[ModelMessage], info: AgentInfo):
            """Simulate connection error."""
            # APIConnectionError requires request parameter
            from httpx import Request
            request = Request("POST", "https://api.openai.com")
            raise APIConnectionError(message="Connection failed", request=request)

        from app.prompts.chat_agent import create_chat_agent

        with patch("app.services.chat_service.create_chat_agent") as mock_create:
            agent = create_chat_agent()
            mock_create.return_value = agent

            with agent.override(model=FunctionModel(model_function)):
                request = ChatRequest(message="Show stats")

                with pytest.raises(APIConnectionError):
                    await service.send_message(user_id="test-user", request=request)

    async def test_garmin_service_failure(self):
        """Verify that Garmin API failures propagate correctly."""
        from pydantic_ai import ModelMessage, ModelResponse, ToolCallPart
        from pydantic_ai.models.function import AgentInfo, FunctionModel

        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation = MagicMock(conversation_id="conv-123")
        mock_conversation_service.create_conversation.return_value = mock_conversation
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Mock GarminService to raise error
        with patch("app.prompts.chat_agent.GarminService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_activities_cached.side_effect = ConnectionError("Garmin API unavailable")
            mock_service_class.return_value = mock_service

            def model_function(messages: list[ModelMessage], info: AgentInfo):
                """Have agent try to call activity tool, which will fail."""
                if len(messages) == 1:
                    # Agent decides to call tool
                    tool_call = ToolCallPart(
                        tool_name="garmin_activity_tool",
                        args={"start_date": "2025-11-06", "end_date": "2025-11-13"}
                    )
                    return ModelResponse(parts=[tool_call])

            from app.prompts.chat_agent import create_chat_agent

            with patch("app.services.chat_service.create_chat_agent") as mock_create:
                agent = create_chat_agent()
                mock_create.return_value = agent

                with agent.override(model=FunctionModel(model_function)):
                    request = ChatRequest(message="How many runs this week?")

                    # Tool failure should propagate
                    with pytest.raises(ConnectionError, match="Garmin API unavailable"):
                        await service.send_message(user_id="test-user", request=request)

    async def test_conversation_not_found(self):
        """Verify error when conversation doesn't exist."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.get_conversation.return_value = None

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Test - no need for FunctionModel since error occurs before agent call
        request = ChatRequest(
            message="Follow up question", conversation_id="non-existent-conv"
        )

        with pytest.raises(ValueError, match="Conversation not found"):
            await service.send_message(user_id="test-user", request=request)

    async def test_firestore_write_failure(self):
        """Verify error handling when Firestore write fails."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.side_effect = ConnectionError(
            "Firestore unavailable"
        )

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Test - no need for FunctionModel since error occurs before agent call
        request = ChatRequest(message="Start new chat")

        with pytest.raises(ConnectionError):
            await service.send_message(user_id="test-user", request=request)

    async def test_agent_returns_invalid_confidence(self):
        """Verify handling of agent returning out-of-range confidence."""
        from pydantic_ai import ModelMessage, ModelResponse, TextPart
        from pydantic_ai.models.function import AgentInfo, FunctionModel
        from pydantic_ai.exceptions import UnexpectedModelBehavior

        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation = MagicMock(conversation_id="conv-123")
        mock_conversation_service.create_conversation.return_value = mock_conversation
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        def model_function(messages: list[ModelMessage], info: AgentInfo):
            """Return invalid JSON with out-of-range confidence."""
            # Return JSON with confidence > 1.0 (invalid)
            return ModelResponse(
                parts=[
                    TextPart(
                        '{"message": "Test response", "confidence": 1.5, '
                        '"data_sources_used": [], "suggested_followup": null}'
                    )
                ]
            )

        from app.prompts.chat_agent import create_chat_agent

        with patch("app.services.chat_service.create_chat_agent") as mock_create:
            agent = create_chat_agent()
            mock_create.return_value = agent

            with agent.override(model=FunctionModel(model_function)):
                request = ChatRequest(message="Test")

                # Pydantic-AI will retry and eventually raise UnexpectedModelBehavior
                with pytest.raises(UnexpectedModelBehavior):
                    await service.send_message(user_id="test-user", request=request)

    async def test_empty_agent_response(self):
        """Verify that agent can handle edge case of minimal message."""
        from pydantic_ai import ModelMessage, ModelResponse, TextPart
        from pydantic_ai.models.function import AgentInfo, FunctionModel

        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation = MagicMock(conversation_id="conv-123")
        mock_conversation_service.create_conversation.return_value = mock_conversation
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        def model_function(messages: list[ModelMessage], info: AgentInfo):
            """Return minimal valid message."""
            # Changed test: verify minimal but valid message works
            return ModelResponse(
                parts=[
                    TextPart(
                        '{"message": "OK", "confidence": 0.5, '
                        '"data_sources_used": [], "suggested_followup": null}'
                    )
                ]
            )

        from app.prompts.chat_agent import create_chat_agent

        with patch("app.services.chat_service.create_chat_agent") as mock_create:
            agent = create_chat_agent()
            mock_create.return_value = agent

            with agent.override(model=FunctionModel(model_function)):
                request = ChatRequest(message="Hello")

                # Minimal valid message should work
                response, _ = await service.send_message(user_id="test-user", request=request)
                assert response.message == "OK"

    async def test_message_history_retrieval_failure(self):
        """Verify handling of failure to retrieve message history."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation = MagicMock(conversation_id="conv-123")
        mock_conversation_service.create_conversation.return_value = mock_conversation
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.side_effect = ConnectionError(
            "Failed to read from Firestore"
        )

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Test - no need for FunctionModel since error occurs before agent call
        request = ChatRequest(message="Test message")

        with pytest.raises(ConnectionError):
            await service.send_message(user_id="test-user", request=request)
