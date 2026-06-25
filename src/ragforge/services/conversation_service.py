from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.ragforge.core.exceptions import DocumentNotFoundError
from src.ragforge.models.conversation import Conversation
from src.ragforge.models.message import Message, MessageRole

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES: int = 20


class ConversationService:
    def create_conversation(
        self, db: Session, user_id: str, title: Optional[str] = None
    ) -> Conversation:
        conversation = Conversation(title=title, user_id=user_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        logger.info(
            "Created new conversational space %s for user context %s",
            conversation.id,
            user_id,
        )
        return conversation

    def get_conversation(
        self, db: Session, conversation_id: str, user_id: str
    ) -> Conversation:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_active.is_(True),
            )
            .first()
        )

        if not conversation:
            raise DocumentNotFoundError(
                f"Requested conversation instance '{conversation_id}' not found"
            )
        return conversation

    def list_conversations(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        conversations = (
            db.query(Conversation)
            .filter(Conversation.is_active.is_(True), Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )
        return [
            {
                "id": c.id,
                "title": c.title,
                "message_count": c.message_count,
                "last_message_at": c.last_message_at.isoformat()
                if c.last_message_at
                else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in conversations
        ]

    def rename_conversation(
        self, db: Session, conversation_id: str, user_id: str, title: str
    ) -> Conversation:
        conversation = self.get_conversation(db, conversation_id, user_id)
        conversation.title = title
        db.commit()
        db.refresh(conversation)
        logger.info(
            "Renamed conversation instance %s onto new heading: %r",
            conversation_id,
            title,
        )
        return conversation

    def delete_conversation(
        self, db: Session, conversation_id: str, user_id: str
    ) -> None:
        conversation = self.get_conversation(db, conversation_id, user_id)
        conversation.deactivate()
        db.commit()
        logger.info(
            "Soft-deleted conversation instance archive track: %s", conversation_id
        )

    def add_message(
        self,
        db: Session,
        conversation_id: str,
        role: MessageRole,
        content: str,
        user_id: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        conversation = self.get_conversation(db, conversation_id, user_id)

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources or [],
        )
        db.add(message)

        # Advance quick trace metadata markers on the parent row workspace
        conversation.update_last_message()
        if conversation.message_count == 1:
            conversation.set_title_from_first_message(content)

        db.commit()
        db.refresh(message)
        return message

    def get_history(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        limit: int = MAX_HISTORY_MESSAGES,
    ) -> List[Dict[str, str]]:
        self.get_conversation(
            db, conversation_id, user_id
        )  # Validate contextual ownership boundaries

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        # Invert order sequences back to standard forward timeline progression layouts
        messages.reverse()
        return [{"role": m.role.value, "content": m.content} for m in messages]

    def get_messages(
        self, db: Session, conversation_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        self.get_conversation(db, conversation_id, user_id)

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        result = []
        for m in messages:
            sources = m.sources or []
            # Extract cited multi-modal image blocks from structural metadata footprints
            images = [
                s["image_base64"]
                for s in sources
                if s.get("type") == "image" and s.get("image_base64")
            ]
            result.append(
                {
                    "id": m.id,
                    "role": m.role.value,
                    "content": m.content,
                    "sources": sources,
                    "images": images,
                    "created_at": m.created_at.isoformat(),
                }
            )
        return result


# Export dynamic tracking singleton reference pointer
conversation_service = ConversationService()
