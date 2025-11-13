"""Chat service orchestrating agent and conversation management."""

import logging

from app.models.chat import ChatRequest, ChatResponse
from app.prompts.chat_agent import create_chat_agent
from app.services.conversation_service import ConversationService
from app.utils.cost_tracking import create_usage_record

logger = logging.getLogger(__name__)


class ChatService:
    """High-level chat service."""

    def __init__(self):
        self.conversation_service = ConversationService()

    async def send_message(
        self, user_id: str, request: ChatRequest
    ) -> tuple[ChatResponse, str]:
        """
        Send chat message and get AI response.

        Args:
            user_id: User ID
            request: Chat request with message and optional conversation_id

        Returns:
            Tuple of (ChatResponse, conversation_id)
        """
        # Create or get conversation
        if request.conversation_id:
            conversation = await self.conversation_service.get_conversation(
                request.conversation_id
            )
            if not conversation:
                raise ValueError("Conversation not found")
            conversation_id = request.conversation_id
        else:
            # Create new conversation
            conversation = await self.conversation_service.create_conversation(
                user_id=user_id
            )
            conversation_id = conversation.conversation_id

        # Save user message
        user_message = await self.conversation_service.add_message(
            conversation_id=conversation_id, role="user", content=request.message
        )

        # Get message history for context
        history = await self.conversation_service.get_message_history(
            conversation_id=conversation_id, limit=10
        )

        # Format history for agent
        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in history[:-1]  # Exclude the message we just added
        ]

        # Run agent
        try:
            agent = create_chat_agent()
            result = await agent.run(
                request.message,
                deps=user_id,  # Pass user_id to tools
                message_history=message_history,
            )

            response = result.data

            # Extract usage for cost tracking
            usage_record = create_usage_record(
                usage_dict=result.usage(), model="gpt-4.1-mini-2025-04-14"
            )

            # Save assistant message with metadata
            await self.conversation_service.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response.message,
                metadata={
                    "model_used": "gpt-4.1-mini-2025-04-14",
                    "tokens": usage_record.model_dump(),
                    "cost_usd": usage_record.cost_usd,
                    "confidence": response.confidence,
                    "data_sources_used": response.data_sources_used,
                },
            )

            # Generate title if first exchange
            if len(history) == 1:  # Only user message
                await self.conversation_service.generate_title(
                    conversation_id=conversation_id, first_user_message=request.message
                )

            logger.info(
                "Chat response generated - conversation: %s, cost: $%.4f",
                conversation_id,
                usage_record.cost_usd,
            )

            return response, conversation_id

        except Exception as e:
            logger.error("Chat agent error: %s", str(e))
            raise
