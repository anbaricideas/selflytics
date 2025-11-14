"""Pydantic-AI chat agent with Garmin data tools."""

import logging
from datetime import date, timedelta
from typing import Any

from google.api_core.exceptions import GoogleAPIError
from pydantic_ai import Agent, RunContext

from app.models.chat import ChatResponse
from app.models.cost_tracking import GPT_4_1_MINI_MODEL
from app.services.garmin_service import GarminService
from app.utils.redact import redact_for_logging


logger = logging.getLogger(__name__)


# Model configuration - add "openai:" prefix for Pydantic-AI
CHAT_MODEL = f"openai:{GPT_4_1_MINI_MODEL}"

# System prompt for fitness insights
CHAT_AGENT_SYSTEM_PROMPT = """You are a fitness data analyst assistant for Selflytics.

Your role:
- Answer user questions about their Garmin fitness data
- Provide insights on trends, patterns, and progress
- Be encouraging but accurate (don't exaggerate progress)
- Use metric units unless user specifies imperial
- Respect privacy (never share data outside conversation)

Available data sources:
- Running, cycling, swimming activities (via garmin_activity_tool)
- Daily metrics: steps, heart rate, sleep, stress (via garmin_metrics_tool)
- User profile information (via garmin_profile_tool)

Guidelines:
- Reference specific dates/activities when possible
- Acknowledge data limitations (e.g., "Based on last 7 days...")
- Keep responses conversational and helpful
- Suggest followup questions when appropriate
- If user asks about data you don't have, explain what's available

Data interpretation tips:
- Resting HR decrease = fitness improvement
- Sleep consistency = important for recovery
- Stress levels: <25 low, 25-50 medium, 50-75 high, >75 very high
- Running pace: faster = lower min/km value
- Activity frequency: 3-5x per week is typical for active users

Always provide:
- Confidence in your analysis (0.0 - 1.0)
- Data sources used (list of tools called)
- Suggested followup question (optional)
"""


async def garmin_activity_tool(
    ctx: RunContext[str],
    start_date: str,
    end_date: str,
    activity_type: str | None = None,
) -> dict[str, Any]:
    """
    Get user activities from Garmin Connect in date range.

    Args:
        ctx: Run context (contains user_id)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        activity_type: Optional activity type filter (running, cycling, swimming)

    Returns:
        Dictionary with activities list and count
    """
    user_id = ctx.deps  # user_id passed as dependency

    service = GarminService(user_id)

    # Parse dates
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    # Fetch activities (uses cache if available)
    activities = await service.get_activities_cached(start, end)

    # Filter by type if specified
    if activity_type:
        activities = [
            a for a in activities if a.get("activity_type", "").lower() == activity_type.lower()
        ]

    # Simplify for AI consumption
    simplified = [
        {
            "date": a.get("start_time_local", "unknown"),
            "type": a.get("activity_type", "unknown"),
            "distance_km": round(a.get("distance_meters", 0) / 1000, 2),
            "duration_min": round(a.get("duration_seconds", 0) / 60, 1),
            "avg_hr": a.get("average_hr"),
            "calories": a.get("calories"),
        }
        for a in activities[:50]  # Limit to 50 for token efficiency
    ]

    return {
        "activities": simplified,
        "total_count": len(activities),
        "date_range": f"{start_date} to {end_date}",
    }


async def garmin_metrics_tool(
    ctx: RunContext[str], metric_type: str, days: int = 7
) -> dict[str, Any]:
    """
    Get daily metrics from Garmin (steps, heart rate, sleep, etc.).

    Args:
        ctx: Run context
        metric_type: Metric type (steps, resting_hr, sleep, stress)
        days: Number of days to retrieve (default: 7)

    Returns:
        Dictionary with metric values and average
    """
    user_id = ctx.deps
    service = GarminService(user_id)

    # Fetch metrics for last N days
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    metrics_list = []
    current_date = start_date

    while current_date <= end_date:
        try:
            metrics = await service.get_daily_metrics_cached(current_date)
            value = None

            # Extract requested metric
            if metric_type == "steps":
                value = metrics.get("steps")
            elif metric_type == "resting_hr":
                value = metrics.get("resting_heart_rate")
            elif metric_type == "sleep":
                value = metrics.get("sleep_seconds", 0) / 3600  # Convert to hours
            elif metric_type == "stress":
                value = metrics.get("avg_stress_level")

            if value is not None:
                metrics_list.append({"date": current_date.isoformat(), "value": value})

        except (GoogleAPIError, KeyError, ValueError) as e:
            logger.debug(
                "Missing data for %s on %s: %s",
                metric_type,
                current_date,
                redact_for_logging(str(e)),
            )
            # Skip days with missing data - this is expected (Firestore errors, missing keys, etc.)

        current_date += timedelta(days=1)

    # Calculate average
    values = [m["value"] for m in metrics_list if m["value"] is not None]
    average = sum(values) / len(values) if values else 0

    return {
        "metric_type": metric_type,
        "days": days,
        "data": metrics_list,
        "average": round(average, 2),
        "unit": _get_metric_unit(metric_type),
    }


async def garmin_profile_tool(ctx: RunContext[str]) -> dict[str, Any]:
    """
    Get user's Garmin profile information.

    Args:
        ctx: Run context

    Returns:
        Dictionary with profile data
    """
    user_id = ctx.deps
    service = GarminService(user_id)

    profile = await service.get_user_profile()  # type: ignore[attr-defined]

    return {
        "display_name": profile.get("display_name", "User"),
        # Email removed to reduce PII exposure - not needed by AI agent
        "garmin_linked": True,
    }


def _get_metric_unit(metric_type: str) -> str:
    """Get unit for metric type."""
    units = {"steps": "steps/day", "resting_hr": "bpm", "sleep": "hours", "stress": "0-100"}
    return units.get(metric_type, "")


def create_chat_agent() -> Agent[str, ChatResponse]:
    """
    Create Pydantic-AI chat agent.

    Returns agent configured with Garmin data tools.
    """
    return Agent(
        model=CHAT_MODEL,
        system_prompt=CHAT_AGENT_SYSTEM_PROMPT,
        output_type=ChatResponse,
        tools=[garmin_activity_tool, garmin_metrics_tool, garmin_profile_tool],
    )
