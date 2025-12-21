"""
Notification service for proactive system events
"""
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import UUID

from app.assistant.models import AssistantSystemEvent


def create_system_event(
    db: Session,
    event_type: str,
    event_data: dict
) -> AssistantSystemEvent:
    """Create a new system event"""
    event = AssistantSystemEvent(
        event_type=event_type,
        event_data=event_data,
        notified=False
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_unnotified_events(
    db: Session,
    limit: int = 10
) -> List[AssistantSystemEvent]:
    """Get unnotified events for polling"""
    return db.query(AssistantSystemEvent).filter(
        AssistantSystemEvent.notified == False
    ).order_by(AssistantSystemEvent.created_at.desc()).limit(limit).all()


def mark_events_as_notified(
    db: Session,
    event_ids: List[UUID]
) -> int:
    """Mark events as notified"""
    count = db.query(AssistantSystemEvent).filter(
        AssistantSystemEvent.id.in_(event_ids)
    ).update({"notified": True}, synchronize_session=False)
    db.commit()
    return count


def cleanup_old_events(
    db: Session,
    retention_hours: int = 24
) -> int:
    """Clean up old notified events"""
    cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
    count = db.query(AssistantSystemEvent).filter(
        AssistantSystemEvent.notified == True,
        AssistantSystemEvent.created_at < cutoff
    ).delete(synchronize_session=False)
    db.commit()
    return count
