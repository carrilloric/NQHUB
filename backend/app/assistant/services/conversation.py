"""
Conversation management service
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.assistant.models import AssistantConversation, AssistantMessage
from app.assistant.schemas import ConversationCreate, MessageCreate


def create_conversation(
    db: Session,
    user_id: int,
    title: Optional[str] = None
) -> AssistantConversation:
    """Create a new conversation"""
    conversation = AssistantConversation(
        user_id=user_id,
        title=title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_user_conversations(
    db: Session,
    user_id: int,
    limit: int = 50
) -> List[AssistantConversation]:
    """Get all conversations for a user"""
    return db.query(AssistantConversation).filter(
        AssistantConversation.user_id == user_id
    ).order_by(AssistantConversation.updated_at.desc()).limit(limit).all()


def get_conversation(
    db: Session,
    conversation_id: UUID,
    user_id: int
) -> Optional[AssistantConversation]:
    """Get a specific conversation with messages"""
    return db.query(AssistantConversation).filter(
        AssistantConversation.id == conversation_id,
        AssistantConversation.user_id == user_id
    ).first()


def add_message(
    db: Session,
    conversation_id: UUID,
    role: str,
    content: str,
    msg_metadata: Optional[dict] = None
) -> AssistantMessage:
    """Add a message to a conversation"""
    message = AssistantMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        msg_metadata=msg_metadata
    )
    db.add(message)

    # Update conversation timestamp
    conversation = db.query(AssistantConversation).filter(
        AssistantConversation.id == conversation_id
    ).first()
    if conversation:
        conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)
    return message


def delete_conversation(
    db: Session,
    conversation_id: UUID,
    user_id: int
) -> bool:
    """Delete a conversation"""
    conversation = db.query(AssistantConversation).filter(
        AssistantConversation.id == conversation_id,
        AssistantConversation.user_id == user_id
    ).first()

    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False
