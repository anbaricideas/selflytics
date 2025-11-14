"""Conversation data models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Conversation(BaseModel):
    """Conversation between user and AI."""

    conversation_id: str
    user_id: str
    title: str = Field(default="New Conversation")  # AI-generated from first message
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    metadata: dict[str, Any] | None = None  # Topics, date ranges queried


class ConversationCreate(BaseModel):
    """Create new conversation."""

    user_id: str
    first_message: str
