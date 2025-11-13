"""Chat data models."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Structured response from chat agent."""

    message: str = Field(..., description="Natural language response to user")
    data_sources_used: list[str] = Field(
        default_factory=list,
        description="Garmin data types queried (activities, metrics, profile)",
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in response accuracy (0.0 - 1.0)"
    )
    suggested_followup: str | None = Field(None, description="Suggested next question for user")


class Message(BaseModel):
    """Chat message in conversation."""

    message_id: str
    conversation_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: dict | None = None  # Tokens, cost, model used


class ChatRequest(BaseModel):
    """Request to send chat message."""

    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None  # Create new if None
