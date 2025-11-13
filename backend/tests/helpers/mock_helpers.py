"""Mock helpers for testing user journeys."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.chat import ChatResponse


@contextmanager
def patch_garmin_service(activities=None, metrics=None, profile=None):
    """
    Mock GarminService responses.

    Args:
        activities: List of activity dicts to return
        metrics: Dict of metric data to return
        profile: User profile dict to return

    Yields:
        Mocked GarminService instance
    """
    with patch("app.services.garmin_service.GarminService") as mock:
        service = AsyncMock()

        if activities is not None:
            service.get_activities_cached.return_value = activities

        if metrics is not None:
            service.get_daily_metrics_cached.return_value = metrics

        if profile is not None:
            service.get_user_profile.return_value = profile

        mock.return_value = service
        yield service


@contextmanager
def patch_openai_agent(response=None, message_history_count=None, usage=None):
    """
    Mock Pydantic-AI agent.

    Args:
        response: ChatResponse to return
        message_history_count: Expected number of history messages (for verification)
        usage: Token usage dict (defaults to small usage)

    Yields:
        Mocked agent instance
    """
    with patch("app.prompts.chat_agent.create_chat_agent") as mock:
        agent = AsyncMock()

        mock_result = MagicMock()
        mock_result.data = response or ChatResponse(
            message="Mocked response",
            data_sources_used=["activities"],
            confidence=0.9,
        )
        mock_result.usage.return_value = usage or {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        }

        if message_history_count is not None:

            def check_history_call(*args, **kwargs):
                history = kwargs.get("message_history", [])
                assert len(history) == message_history_count, (
                    f"Expected {message_history_count} history messages, got {len(history)}"
                )
                return mock_result

            agent.run.side_effect = check_history_call
        else:
            agent.run.return_value = mock_result

        mock.return_value = agent
        yield agent


@contextmanager
def patch_firestore(conversation=None, messages=None):
    """
    Mock Firestore client responses.

    Args:
        conversation: Conversation object to return
        messages: List of Message objects to return

    Yields:
        Mocked Firestore client
    """
    with patch("app.db.firestore_client.get_firestore_client") as mock:
        db = MagicMock()
        collection = MagicMock()
        db.collection.return_value = collection

        if conversation:
            doc_ref = MagicMock()
            doc = MagicMock()
            doc.exists = True
            doc.to_dict.return_value = conversation.model_dump()
            doc_ref.get.return_value = doc
            collection.document.return_value = doc_ref

        if messages:
            # Mock subcollection for messages
            messages_collection = MagicMock()
            messages_docs = []
            for msg in messages:
                doc = MagicMock()
                doc.to_dict.return_value = msg.model_dump()
                messages_docs.append(doc)

            messages_query = MagicMock()
            messages_query.stream.return_value = reversed(messages_docs)
            messages_collection.order_by.return_value.limit.return_value = messages_query
            doc_ref.collection.return_value = messages_collection

        mock.return_value = db
        yield db


def create_mock_conversation(user_id, messages, title="Test Conversation"):
    """
    Create a mock conversation with message history.

    Args:
        user_id: User ID
        messages: List of dicts with 'role' and 'content'
        title: Conversation title

    Returns:
        Conversation object with messages
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from app.models.chat import Message
    from app.models.conversation import Conversation

    conversation_id = str(uuid4())
    now = datetime.now(UTC)

    conversation = Conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        title=title,
        created_at=now,
        updated_at=now,
        message_count=len(messages),
    )

    message_objects = [
        Message(
            message_id=str(uuid4()),
            conversation_id=conversation_id,
            role=msg["role"],
            content=msg["content"],
            timestamp=now,
        )
        for msg in messages
    ]

    return conversation, message_objects
