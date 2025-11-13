"""Conversation management service."""

import uuid
from datetime import UTC, datetime

from google.cloud.firestore_v1 import Increment

from app.db.firestore_client import get_firestore_client
from app.models.chat import Message
from app.models.conversation import Conversation


class ConversationService:
    """Manage chat conversations."""

    def __init__(self):
        self.db = get_firestore_client()
        self.conversations_collection = self.db.collection("conversations")

    async def create_conversation(self, user_id: str) -> Conversation:
        """Create new conversation."""
        conversation_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Create conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title="New Conversation",  # Will update after AI response
            created_at=now,
            updated_at=now,
            message_count=0,
        )

        # Save to Firestore
        self.conversations_collection.document(conversation_id).set(conversation.model_dump())

        return conversation

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Add message to conversation atomically."""
        message_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        message = Message(
            message_id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=now,
            metadata=metadata or {},
        )

        # Use batch write for atomicity - ensures both message creation
        # and conversation update succeed together or both fail
        batch = self.db.batch()

        # Add message to subcollection
        message_ref = (
            self.conversations_collection.document(conversation_id)
            .collection("messages")
            .document(message_id)
        )
        batch.set(message_ref, message.model_dump())

        # Update conversation metadata
        conv_ref = self.conversations_collection.document(conversation_id)
        batch.update(conv_ref, {"updated_at": now, "message_count": Increment(1)})

        # Commit both operations atomically
        batch.commit()

        return message

    async def get_message_history(self, conversation_id: str, limit: int = 10) -> list[Message]:
        """Get last N messages for conversation context."""
        messages_ref = (
            self.conversations_collection.document(conversation_id)
            .collection("messages")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )

        messages = [Message(**doc.to_dict()) for doc in messages_ref.stream()]

        # Return chronological order
        return list(reversed(messages))

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID."""
        doc = self.conversations_collection.document(conversation_id).get()
        if doc.exists:
            return Conversation(**doc.to_dict())
        return None

    async def list_conversations(self, user_id: str, limit: int = 20) -> list[Conversation]:
        """List user's conversations."""
        query = (
            self.conversations_collection.where("user_id", "==", user_id)
            .order_by("updated_at", direction="DESCENDING")
            .limit(limit)
        )

        return [Conversation(**doc.to_dict()) for doc in query.stream()]

    async def generate_title(self, conversation_id: str, first_user_message: str):
        """Generate conversation title from first message (AI-powered)."""
        # Simple heuristic for now - use first 50 chars
        title = first_user_message[:50]
        if len(first_user_message) > 50:
            title += "..."

        # Update conversation
        self.conversations_collection.document(conversation_id).update({"title": title})
