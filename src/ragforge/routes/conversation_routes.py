import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.ragforge.dependencies.auth import get_current_user
from src.ragforge.dependencies.db import get_db
from src.ragforge.models.user import User
from src.ragforge.schemas.conversation import (
    ChatRequest,
    ConversationResponse,
    CreateConversationRequest,
    DeleteConversationResponse,
    RenameConversationRequest,
)
from src.ragforge.services.conversation_service import conversation_service
from src.ragforge.services.streaming_service import stream_chat_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization credentials"
        }
    },
)
def create_conversation(
    payload: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = conversation_service.create_conversation(
        db, user_id=current_user.id, title=payload.title
    )
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
    }


@router.get(
    "",
    summary="List all conversations",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization credentials"
        }
    },
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conversation_service.list_conversations(db, user_id=current_user.id)


@router.get(
    "/{conversation_id}/messages",
    summary="Get conversation messages",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization credentials"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Target conversation thread reference missing or unaccessible"
        },
    },
)
def get_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conversation_service.get_messages(
        db, conversation_id, user_id=current_user.id
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Rename a conversation",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization credentials"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Target conversation thread reference missing or unaccessible"
        },
    },
)
def rename_conversation(
    conversation_id: str,
    payload: RenameConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = conversation_service.rename_conversation(
        db, conversation_id, user_id=current_user.id, title=payload.title
    )
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
    }


@router.post(
    "/{conversation_id}/ask",
    summary="Ask a question - streams response token-by-token via SSE",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization credentials"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Target conversation thread reference missing or unaccessible"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Downstream model parsing context window constraint error"
        },
    },
)
async def ask_in_conversation(
    conversation_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a question parameter - streams the complete RAG execution answer tokens via Server-Sent Events.

    Loads the 20 most recent multi-turn messages automatically to preserve continuity constraints.
    """
    logger.info(
        "Conversational execution frame requested for thread room: %s", conversation_id
    )
    return StreamingResponse(
        stream_chat_response(
            question=payload.question,
            user_id=current_user.id,
            db=db,
            conversation_id=conversation_id,
            doc_ids=payload.doc_ids,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete(
    "/{conversation_id}",
    response_model=DeleteConversationResponse,
    summary="Delete a conversation",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization credentials"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Target conversation thread reference missing or unaccessible"
        },
    },
)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation_service.delete_conversation(
        db, conversation_id, user_id=current_user.id
    )
    return {"message": "Conversation deleted", "id": conversation_id}
