"""
FastAPI routes for AI Assistant

NOTE: Currently using sync DB session (get_db_sync) for simplicity.
TODO: Migrate to async when integrating with auth system.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db_sync
# from app.core.deps import get_current_user  # TODO: Enable when fixing async
from app.models.user import User
from app.assistant import schemas
from app.assistant.services import conversation as conv_service
from app.assistant.services import notifications as notif_service
from app.assistant.services.orchestrator import get_orchestrator
from app.assistant.tools import status_monitor, system_health

router = APIRouter(prefix="/assistant")


# Temporary mock user for testing (TODO: Remove when auth is fixed)
def get_mock_user() -> User:
    user = User()
    user.id = 1
    user.email = "test@nqhub.com"
    user.full_name = "Test User"
    return user


# ============== Chat Endpoints ==============

@router.post("/query", response_model=schemas.ChatResponse)
def query(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)  # TODO: Use get_current_user when auth is fixed
):
    """
    Simplified endpoint for direct queries (alias for /chat)
    Used by the frontend dashboard for quick Vanna queries
    """
    return chat(request, db, current_user)


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)  # TODO: Use get_current_user when auth is fixed
):
    """
    Send a message to the assistant
    """
    orchestrator = get_orchestrator()

    # Get or create conversation
    if request.conversation_id:
        conversation = conv_service.get_conversation(db, request.conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = conv_service.create_conversation(db, current_user.id)

    # Get conversation history for context
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages[-10:]  # Last 10 messages
    ]

    # Add user message
    user_message = conv_service.add_message(
        db,
        conversation.id,
        role="user",
        content=request.message
    )

    # Process with orchestrator
    response = orchestrator.process_message(
        user_message=request.message,
        user_id=str(current_user.id),
        db=db,
        conversation_history=conversation_history
    )

    # Add assistant message
    assistant_message = conv_service.add_message(
        db,
        conversation.id,
        role="assistant",
        content=response["content"],
        msg_metadata=response.get("metadata")
    )

    return schemas.ChatResponse(
        conversation_id=conversation.id,
        user_message=user_message,
        assistant_message=assistant_message,
        metadata=response.get("metadata")
    )


# ============== Conversation Endpoints ==============

@router.get("/conversations", response_model=List[schemas.ConversationListItem])
def list_conversations(
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Get all conversations for current user"""
    conversations = conv_service.get_user_conversations(db, current_user.id)

    result = []
    for conv in conversations:
        last_msg = conv.messages[-1] if conv.messages else None
        result.append(schemas.ConversationListItem(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages),
            last_message_preview=last_msg.content[:100] if last_msg else None
        ))

    return result


@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationResponse)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Get a specific conversation with all messages"""
    conversation = conv_service.get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Delete a conversation"""
    success = conv_service.delete_conversation(db, conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


# ============== System Events (Notifications) ==============

@router.get("/events", response_model=List[schemas.SystemEventResponse])
def get_system_events(
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Get unnotified system events (for polling)"""
    events = notif_service.get_unnotified_events(db, limit=10)
    return events


@router.post("/events/mark-read", status_code=status.HTTP_204_NO_CONTENT)
def mark_events_read(
    request: schemas.MarkEventsReadRequest,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Mark events as notified"""
    notif_service.mark_events_as_notified(db, request.event_ids)
    return None


# ============== Status Endpoints ==============

@router.get("/status/etl", response_model=schemas.ETLStatusResponse)
def get_etl_status(
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Get ETL status"""
    return status_monitor.get_etl_status(db)


@router.get("/status/patterns", response_model=schemas.PatternStatusResponse)
def get_pattern_status(
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Get pattern detection status"""
    return status_monitor.get_pattern_status(db)


@router.get("/status/database", response_model=schemas.DatabaseStatsResponse)
def get_database_status(
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """Get database statistics"""
    return status_monitor.get_database_stats(db)


@router.get("/status/system", response_model=schemas.SystemHealthResponse)
def get_system_status(
    current_user: User = Depends(get_mock_user)
):
    """Get system health"""
    return system_health.get_system_health()


# ============== Feedback Endpoint ==============

@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(
    request: schemas.FeedbackRequest,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_mock_user)
):
    """
    Submit feedback on assistant response
    (Can be used to improve Vanna training in future)
    """
    # TODO: Store feedback in database
    # For now, just acknowledge
    return None
