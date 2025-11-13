"""Test that agent correctly calls tools based on user queries.

Uses Pydantic-AI's FunctionModel to test agent tool orchestration without external API calls.
"""

import os
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.models.chat import ChatRequest
from app.services.chat_service import ChatService

# Set dummy API key to prevent OpenAI client initialization errors
# This allows agent creation without making actual API calls (FunctionModel will handle requests)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing-only")


@pytest.mark.asyncio
class TestChatToolCalling:
    """Test agent tool calling logic using FunctionModel."""

    async def test_activity_query_calls_activity_tool(self):
        """Verify 'how many runs' triggers garmin_activity_tool with correct date range."""

        # Track tool calls
        tool_calls_made = []

        # Mock GarminService.get_activities_cached (simpler than mocking the client)
        with patch("app.services.garmin_service.GarminService.get_activities_cached") as mock_get_activities:
            mock_get_activities.return_value = [
                {
                    "start_time_local": "2025-11-10T06:00:00",
                    "activity_type": "running",
                    "distance_meters": 5000,
                    "duration_seconds": 1800,
                    "average_hr": 150,
                    "calories": 350,
                }
            ]

            # Define model function to control agent behavior
            def model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
                """Control agent to call garmin_activity_tool for runs query."""
                # First call: LLM decides to call tool
                if len(messages) == 1:
                    # Calculate date range for "this week"
                    end_date = date.today()
                    start_date = end_date - timedelta(days=7)

                    tool_call = ToolCallPart(
                        tool_name="garmin_activity_tool",
                        args={
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "activity_type": "running",
                        },
                    )
                    tool_calls_made.append(tool_call.args)
                    return ModelResponse(parts=[tool_call])

                # Second call: LLM responds after tool returns
                else:
                    tool_return = messages[-1].parts[0]
                    assert tool_return.part_kind == "tool-return"
                    return ModelResponse(
                        parts=[
                            TextPart(
                                '{"message": "You had 1 run this week covering 5km.", '
                                '"data_sources_used": ["activities"], '
                                '"confidence": 0.9, '
                                '"suggested_followup": "What was your average pace?"}'
                            )
                        ]
                    )

            # Mock conversation service
            mock_conversation_service = AsyncMock()
            mock_conversation = MagicMock(conversation_id="conv-123", user_id="user-456")
            mock_conversation_service.create_conversation.return_value = mock_conversation
            mock_conversation_service.add_message.return_value = AsyncMock()
            mock_conversation_service.get_message_history.return_value = []

            # Execute with FunctionModel override
            from app.prompts.chat_agent import create_chat_agent

            service = ChatService()
            service.conversation_service = mock_conversation_service

            # Create agent and override with FunctionModel before using
            with patch("app.services.chat_service.create_chat_agent") as mock_create:
                agent = create_chat_agent()
                mock_create.return_value = agent

                # Override the agent's model with our FunctionModel
                with agent.override(model=FunctionModel(model_function)):
                    request = ChatRequest(message="How many runs did I do this week?")
                    response, conv_id = await service.send_message(user_id="test-user", request=request)

                # Verify tool was called with correct arguments
                assert len(tool_calls_made) == 1, "garmin_activity_tool should have been called once"
                tool_args = tool_calls_made[0]

                assert "start_date" in tool_args
                assert "end_date" in tool_args
                assert tool_args["activity_type"] == "running"

                # Verify date range is approximately "this week"
                start = date.fromisoformat(tool_args["start_date"])
                end = date.fromisoformat(tool_args["end_date"])
                assert (end - start).days <= 7

                # Verify GarminService.get_activities_cached was called
                mock_get_activities.assert_called_once()

                # Verify response
                assert "run" in response.message.lower()
                assert "activities" in response.data_sources_used

    async def test_metrics_query_calls_metrics_tool(self):
        """Verify 'show my steps' triggers garmin_metrics_tool with correct metric type."""

        tool_calls_made = []

        # Mock GarminService
        with patch("app.services.garmin_service.GarminService") as mock_garmin_class:
            mock_garmin = AsyncMock()
            mock_garmin.get_daily_metrics_cached.return_value = {"steps": 8500}
            mock_garmin_class.return_value = mock_garmin

            def model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
                """Control agent to call garmin_metrics_tool for steps query."""
                if len(messages) == 1:
                    tool_call = ToolCallPart(
                        tool_name="garmin_metrics_tool",
                        args={"metric_type": "steps", "days": 7},
                    )
                    tool_calls_made.append(tool_call.args)
                    return ModelResponse(parts=[tool_call])
                else:
                    return ModelResponse(
                        parts=[
                            TextPart(
                                '{"message": "Your average steps: 8,500/day", '
                                '"data_sources_used": ["metrics"], '
                                '"confidence": 0.85, '
                                '"suggested_followup": null}'
                            )
                        ]
                    )

            # Mock conversation service
            mock_conversation_service = AsyncMock()
            mock_conversation = MagicMock(conversation_id="conv-123")
            mock_conversation_service.create_conversation.return_value = mock_conversation
            mock_conversation_service.add_message.return_value = AsyncMock()
            mock_conversation_service.get_message_history.return_value = []

            with patch("app.services.chat_service.create_chat_agent") as mock_create_agent:
                from app.prompts.chat_agent import create_chat_agent

                real_agent = create_chat_agent()
                real_agent._model = FunctionModel(model_function)
                mock_create_agent.return_value = real_agent

                service = ChatService()
                service.conversation_service = mock_conversation_service

                request = ChatRequest(message="Show me my step count for the last week")
                response, _ = await service.send_message(user_id="test-user", request=request)

                # Verify tool was called
                assert len(tool_calls_made) == 1
                assert tool_calls_made[0]["metric_type"] == "steps"
                assert tool_calls_made[0]["days"] == 7

                # Verify GarminService was called
                assert mock_garmin.get_daily_metrics_cached.called

                # Verify response
                assert "metrics" in response.data_sources_used

    async def test_recovery_query_calls_multiple_tools(self):
        """Verify 'am I recovering well' can call multiple metrics tools."""

        tool_calls_made = []

        # Mock GarminService
        with patch("app.services.garmin_service.GarminService") as mock_garmin_class:
            mock_garmin = AsyncMock()

            def get_metrics(metric_date):
                """Return different metrics based on date."""
                return {"resting_heart_rate": 65, "sleep_seconds": 27000, "steps": 8500}

            mock_garmin.get_daily_metrics_cached.side_effect = get_metrics
            mock_garmin_class.return_value = mock_garmin

            call_count = 0

            def model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
                """Control agent to call multiple metrics tools for recovery query."""
                nonlocal call_count

                # First call: request resting HR
                if call_count == 0:
                    call_count += 1
                    tool_call = ToolCallPart(
                        tool_name="garmin_metrics_tool",
                        args={"metric_type": "resting_hr", "days": 7},
                    )
                    tool_calls_made.append({"tool": "metrics", "args": tool_call.args})
                    return ModelResponse(parts=[tool_call])

                # Second call: request sleep after HR return
                elif call_count == 1:
                    call_count += 1
                    tool_call = ToolCallPart(
                        tool_name="garmin_metrics_tool",
                        args={"metric_type": "sleep", "days": 7},
                    )
                    tool_calls_made.append({"tool": "metrics", "args": tool_call.args})
                    return ModelResponse(parts=[tool_call])

                # Third call: final response
                else:
                    return ModelResponse(
                        parts=[
                            TextPart(
                                '{"message": "Recovery looks good: HR 65bpm, sleep 7.5hr/night", '
                                '"data_sources_used": ["metrics"], '
                                '"confidence": 0.88, '
                                '"suggested_followup": null}'
                            )
                        ]
                    )

            # Mock conversation service
            mock_conversation_service = AsyncMock()
            mock_conversation = MagicMock(conversation_id="conv-123")
            mock_conversation_service.create_conversation.return_value = mock_conversation
            mock_conversation_service.add_message.return_value = AsyncMock()
            mock_conversation_service.get_message_history.return_value = []

            with patch("app.services.chat_service.create_chat_agent") as mock_create_agent:
                from app.prompts.chat_agent import create_chat_agent

                real_agent = create_chat_agent()
                real_agent._model = FunctionModel(model_function)
                mock_create_agent.return_value = real_agent

                service = ChatService()
                service.conversation_service = mock_conversation_service

                request = ChatRequest(message="Am I recovering well?")
                response, _ = await service.send_message(user_id="test-user", request=request)

                # Verify multiple tools were called
                assert len(tool_calls_made) == 2, "Should call metrics tool twice"

                metric_types = [call["args"]["metric_type"] for call in tool_calls_made]
                assert "resting_hr" in metric_types
                assert "sleep" in metric_types

                # Verify response mentions recovery
                assert "recovery" in response.message.lower() or "hr" in response.message.lower()

    async def test_profile_query_calls_profile_tool(self):
        """Verify 'what's my profile' triggers garmin_profile_tool."""

        tool_calls_made = []

        # Mock GarminService
        with patch("app.services.garmin_service.GarminService") as mock_garmin_class:
            mock_garmin = AsyncMock()
            mock_garmin.get_user_profile.return_value = {
                "display_name": "Test User",
                "email": "test@example.com",
            }
            mock_garmin_class.return_value = mock_garmin

            def model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
                """Control agent to call garmin_profile_tool."""
                if len(messages) == 1:
                    tool_call = ToolCallPart(tool_name="garmin_profile_tool", args={})
                    tool_calls_made.append("profile")
                    return ModelResponse(parts=[tool_call])
                else:
                    return ModelResponse(
                        parts=[
                            TextPart(
                                '{"message": "Your profile: Test User (test@example.com)", '
                                '"data_sources_used": ["profile"], '
                                '"confidence": 1.0, '
                                '"suggested_followup": null}'
                            )
                        ]
                    )

            # Mock conversation service
            mock_conversation_service = AsyncMock()
            mock_conversation = MagicMock(conversation_id="conv-123")
            mock_conversation_service.create_conversation.return_value = mock_conversation
            mock_conversation_service.add_message.return_value = AsyncMock()
            mock_conversation_service.get_message_history.return_value = []

            with patch("app.services.chat_service.create_chat_agent") as mock_create_agent:
                from app.prompts.chat_agent import create_chat_agent

                real_agent = create_chat_agent()
                real_agent._model = FunctionModel(model_function)
                mock_create_agent.return_value = real_agent

                service = ChatService()
                service.conversation_service = mock_conversation_service

                request = ChatRequest(message="What's my Garmin profile?")
                response, _ = await service.send_message(user_id="test-user", request=request)

                # Verify tool was called
                assert len(tool_calls_made) == 1
                assert tool_calls_made[0] == "profile"

                # Verify GarminService.get_user_profile was called
                mock_garmin.get_user_profile.assert_called_once()

                # Verify response
                assert "profile" in response.data_sources_used
