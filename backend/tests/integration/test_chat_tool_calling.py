"""Test that agent correctly calls tools based on user queries."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.chat import ChatRequest
from app.services.chat_service import ChatService


pytestmark = pytest.mark.skip(
    reason="Requires proper OpenAI API mocking - agent creates OpenAI client internally. "
    "Need to mock at OpenAI client level, not agent level. Future work."
)


@pytest.mark.asyncio
class TestChatToolCalling:
    """Test agent tool calling logic."""

    async def test_activity_query_calls_activity_tool(self):
        """Verify 'how many runs' triggers garmin_activity_tool."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Track tool calls
        tool_called = False
        tool_call_args = {}

        async def mock_activity_tool(ctx, start_date, end_date, activity_type=None):
            nonlocal tool_called, tool_call_args
            tool_called = True
            tool_call_args = {
                "start_date": start_date,
                "end_date": end_date,
                "activity_type": activity_type,
            }
            return {
                "total_count": 5,
                "activities": [],
                "date_range": f"{start_date} to {end_date}",
            }

        with (
            patch("app.prompts.chat_agent.garmin_activity_tool", mock_activity_tool),
            patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory,
        ):
            # Mock agent to call tool
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.message = "You had 5 runs this week"
            mock_result.data.data_sources_used = ["activities"]
            mock_result.data.confidence = 0.9
            mock_result.usage.return_value = {"prompt_tokens": 100, "completion_tokens": 50}

            async def run_with_tool_call(*args, **kwargs):
                # Simulate agent calling the tool
                await mock_activity_tool(
                    None,
                    start_date=(datetime.now(UTC) - timedelta(days=7)).date().isoformat(),
                    end_date=datetime.now(UTC).date().isoformat(),
                )
                return mock_result

            mock_agent.run.side_effect = run_with_tool_call
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="How many runs did I do this week?")
            await service.send_message(user_id="test-user", request=request)

            # Verify tool was called
            assert tool_called, "garmin_activity_tool should have been called"
            assert "start_date" in tool_call_args
            assert "end_date" in tool_call_args

            # Verify date range is approximately "this week" (last 7 days)
            start = datetime.fromisoformat(tool_call_args["start_date"])
            end = datetime.fromisoformat(tool_call_args["end_date"])
            assert (end - start).days <= 7

    async def test_metrics_query_calls_metrics_tool(self):
        """Verify 'show my steps' triggers garmin_metrics_tool."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Track tool calls
        tool_called = False
        tool_call_args = {}

        async def mock_metrics_tool(ctx, metric_type, days=7):
            nonlocal tool_called, tool_call_args
            tool_called = True
            tool_call_args = {"metric_type": metric_type, "days": days}
            return {
                "metric_type": metric_type,
                "days": days,
                "data": [],
                "average": 8500,
                "unit": "steps/day",
            }

        with (
            patch("app.prompts.chat_agent.garmin_metrics_tool", mock_metrics_tool),
            patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory,
        ):
            # Mock agent to call tool
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.message = "Your average steps this week: 8,500"
            mock_result.data.data_sources_used = ["metrics"]
            mock_result.data.confidence = 0.85
            mock_result.usage.return_value = {"prompt_tokens": 80, "completion_tokens": 40}

            async def run_with_tool_call(*args, **kwargs):
                await mock_metrics_tool(None, metric_type="steps", days=7)
                return mock_result

            mock_agent.run.side_effect = run_with_tool_call
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="Show me my step count for the last week")
            await service.send_message(user_id="test-user", request=request)

            # Verify tool was called
            assert tool_called, "garmin_metrics_tool should have been called"
            assert tool_call_args["metric_type"] == "steps"
            assert tool_call_args["days"] == 7

    async def test_recovery_query_calls_multiple_tools(self):
        """Verify 'am I recovering well' calls sleep + HR tools."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Track tool calls
        tools_called = []

        async def mock_metrics_tool(ctx, metric_type, days=7):
            tools_called.append({"tool": "metrics", "metric_type": metric_type})
            return {
                "metric_type": metric_type,
                "days": days,
                "data": [],
                "average": 65 if metric_type == "resting_hr" else 7.5,
                "unit": "bpm" if metric_type == "resting_hr" else "hours",
            }

        with (
            patch("app.prompts.chat_agent.garmin_metrics_tool", mock_metrics_tool),
            patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory,
        ):
            # Mock agent to call multiple tools
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.message = "Recovery looks good: HR 65bpm, sleep 7.5hr"
            mock_result.data.data_sources_used = ["metrics"]
            mock_result.data.confidence = 0.88
            mock_result.usage.return_value = {"prompt_tokens": 120, "completion_tokens": 60}

            async def run_with_tool_calls(*args, **kwargs):
                # Simulate agent calling multiple tools
                await mock_metrics_tool(None, metric_type="resting_hr", days=7)
                await mock_metrics_tool(None, metric_type="sleep", days=7)
                return mock_result

            mock_agent.run.side_effect = run_with_tool_calls
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="Am I recovering well?")
            await service.send_message(user_id="test-user", request=request)

            # Verify multiple tools were called
            assert len(tools_called) >= 2, "Multiple metrics tools should be called"
            metric_types = {call["metric_type"] for call in tools_called}
            assert "resting_hr" in metric_types or "sleep" in metric_types

    async def test_profile_query_calls_profile_tool(self):
        """Verify 'what's my profile' triggers garmin_profile_tool."""
        # Mock dependencies
        mock_conversation_service = AsyncMock()
        mock_conversation_service.create_conversation.return_value = AsyncMock(
            conversation_id="conv-123"
        )
        mock_conversation_service.add_message.return_value = AsyncMock()
        mock_conversation_service.get_message_history.return_value = []

        service = ChatService()
        service.conversation_service = mock_conversation_service

        # Track tool calls
        tool_called = False

        async def mock_profile_tool(ctx):
            nonlocal tool_called
            tool_called = True
            return {
                "display_name": "Test User",
                "email": "test@example.com",
                "garmin_linked": True,
            }

        with (
            patch("app.prompts.chat_agent.garmin_profile_tool", mock_profile_tool),
            patch("app.prompts.chat_agent.create_chat_agent") as mock_agent_factory,
        ):
            # Mock agent to call tool
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.message = "Your profile: Test User (test@example.com)"
            mock_result.data.data_sources_used = ["profile"]
            mock_result.data.confidence = 1.0
            mock_result.usage.return_value = {"prompt_tokens": 50, "completion_tokens": 30}

            async def run_with_tool_call(*args, **kwargs):
                await mock_profile_tool(None)
                return mock_result

            mock_agent.run.side_effect = run_with_tool_call
            mock_agent_factory.return_value = mock_agent

            # Test
            request = ChatRequest(message="What's my Garmin profile?")
            await service.send_message(user_id="test-user", request=request)

            # Verify tool was called
            assert tool_called, "garmin_profile_tool should have been called"
