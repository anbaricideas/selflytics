"""Pydantic-AI chat agent for fitness insights."""

import os
from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext


class ChatResponse(BaseModel):
    """Structured response from chat agent."""

    message: str = Field(..., description="Natural language response")
    data_sources_used: list[str] = Field(
        default_factory=list, description="Data types queried"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in accuracy")
    suggested_followup: Optional[str] = Field(
        None, description="Suggested next question"
    )


# Mock tool implementations (will connect to real Garmin data in Step 3)
async def get_activities_tool(
    ctx: RunContext[str], start_date: str, end_date: str
) -> dict:
    """Get activities in date range (mock data)."""
    return {
        "activities": [
            {
                "date": "2025-11-09",
                "type": "running",
                "distance_km": 5.2,
                "duration_min": 32,
                "avg_pace_min_km": 6.15,
            },
            {
                "date": "2025-11-07",
                "type": "running",
                "distance_km": 8.0,
                "duration_min": 52,
                "avg_pace_min_km": 6.30,
            },
        ],
        "total_count": 2,
    }


async def get_metrics_tool(ctx: RunContext[str], metric_type: str, days: int) -> dict:
    """Get daily metrics (mock data)."""
    return {
        "metric": metric_type,
        "days": days,
        "average": 12500 if metric_type == "steps" else 7.5,
        "unit": "steps/day" if metric_type == "steps" else "hours",
    }


# Create agent - use TestModel if OPENAI_API_KEY not set
def _get_model():
    """Get model based on environment configuration."""
    if os.getenv("OPENAI_API_KEY"):
        return "openai:gpt-4o-mini"
    else:
        # Use TestModel for development/testing without API key
        from pydantic_ai.models.test import TestModel

        return TestModel()


chat_agent = Agent(
    model=_get_model(),
    system_prompt="""You are a fitness data analyst assistant for Selflytics.

Your role:
- Answer user questions about their Garmin fitness data
- Provide insights on trends, patterns, and progress
- Be encouraging but accurate (don't exaggerate progress)
- Use metric units unless user specifies imperial

Available data:
- Running, cycling, swimming activities
- Steps, heart rate, sleep metrics

Guidelines:
- Reference specific dates/activities when possible
- Acknowledge data limitations (e.g., "Based on last 7 days...")
- Keep responses conversational and helpful
""",
    output_type=ChatResponse,
    tools=[get_activities_tool, get_metrics_tool],
)


async def run_chat(message: str, user_id: str) -> ChatResponse:
    """Run chat agent and return structured response."""
    result = await chat_agent.run(message, deps=user_id)
    return result.output
