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


# Initialize Garmin client (module level for spike simplicity)
from spike.garmin_client import GarminClient

_garmin_client: GarminClient | None = None


def get_garmin_client() -> GarminClient:
    """Get or create Garmin client instance."""
    global _garmin_client
    if _garmin_client is None:
        _garmin_client = GarminClient()
    return _garmin_client


# Tool implementations (connected to Garmin data)
async def get_activities_tool(
    ctx: RunContext[str], start_date: str, end_date: str
) -> dict:
    """Get activities in date range from Garmin Connect."""
    garmin_client = get_garmin_client()

    # Parse dates
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    # Check if authenticated
    if not garmin_client.authenticated:
        # Return mock data if not authenticated (for testing without Garmin account)
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
            "note": "Mock data - Garmin not authenticated",
        }

    # Fetch real activities
    activities = await garmin_client.get_activities(start, end)

    # Simplify response for AI (extract key fields)
    return {
        "activities": [
            {
                "date": a.get("startTimeLocal", "unknown"),
                "type": a.get("activityType", {}).get("typeKey", "unknown"),
                "distance_km": a.get("distance", 0) / 1000 if a.get("distance") else 0,
                "duration_min": a.get("duration", 0) / 60 if a.get("duration") else 0,
                "calories": a.get("calories", 0),
                "avg_hr": a.get("averageHR"),
            }
            for a in activities
        ],
        "total_count": len(activities),
    }


async def get_metrics_tool(ctx: RunContext[str], metric_type: str, days: int) -> dict:
    """Get daily metrics from Garmin Connect."""
    garmin_client = get_garmin_client()

    # Check if authenticated
    if not garmin_client.authenticated:
        # Return mock data if not authenticated
        return {
            "metric": metric_type,
            "days": days,
            "average": 12500 if metric_type == "steps" else 7.5,
            "unit": "steps/day" if metric_type == "steps" else "hours",
            "note": "Mock data - Garmin not authenticated",
        }

    # Fetch real metrics for today (spike simplified - only today's data)
    try:
        today_metrics = await garmin_client.get_daily_metrics(date.today())

        # Extract requested metric
        if metric_type == "steps":
            value = today_metrics.get("totalSteps", 0)
            unit = "steps"
        elif metric_type == "distance":
            value = today_metrics.get("totalDistanceMeters", 0) / 1000  # Convert to km
            unit = "km"
        elif metric_type == "calories":
            value = today_metrics.get("totalKilocalories", 0)
            unit = "kcal"
        else:
            value = 0
            unit = "unknown"

        return {
            "metric": metric_type,
            "days": 1,  # Spike only fetches today
            "value": value,
            "unit": unit,
            "date": date.today().isoformat(),
        }
    except Exception as e:
        return {"error": f"Failed to fetch metrics: {e}"}


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
