"""Chat API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.models.chat import ChatRequest
from app.models.user import UserResponse
from app.services.chat_service import ChatService


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/", response_class=HTMLResponse)
async def chat_page(
    request: Request, current_user: UserResponse = Depends(get_current_user)
) -> Any:
    """Render chat interface page."""
    return templates.TemplateResponse("chat.html", {"request": request, "user": current_user})


@router.post("/send")
async def send_message(
    request: ChatRequest, current_user: UserResponse = Depends(get_current_user)
) -> dict[str, Any]:
    """Send chat message and get AI response."""
    service = ChatService()

    try:
        response, conversation_id = await service.send_message(
            user_id=current_user.user_id, request=request
        )

        return {"conversation_id": conversation_id, "response": response.model_dump()}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/conversations")
async def list_conversations(
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, list[dict[str, Any]]]:
    """List user's conversations."""
    service = ChatService()
    conversations = await service.conversation_service.list_conversations(
        user_id=current_user.user_id
    )

    return {"conversations": [c.model_dump() for c in conversations]}


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str, current_user: UserResponse = Depends(get_current_user)
) -> dict[str, Any]:
    """Get conversation with messages."""
    service = ChatService()

    conversation = await service.conversation_service.get_conversation(conversation_id)

    if not conversation or conversation.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = await service.conversation_service.get_message_history(
        conversation_id=conversation_id,
        limit=100,  # All messages for display
    )

    return {
        "conversation": conversation.model_dump(),
        "messages": [m.model_dump() for m in messages],
    }


# TODO (Phase 4): Implement DELETE /chat/{conversation_id} endpoint
# Should include ownership validation and cascade delete of messages subcollection
