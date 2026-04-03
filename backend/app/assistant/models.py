"""
SQLAlchemy models for the AI Assistant
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class AssistantConversation(Base):
    """Conversation threads between user and assistant"""
    __tablename__ = "assistant_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship("AssistantMessage", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", backref="assistant_conversations")

    def __repr__(self):
        return f"<AssistantConversation(id={self.id}, user_id={self.user_id}, title={self.title})>"


class AssistantMessage(Base):
    """Individual messages within a conversation"""
    __tablename__ = "assistant_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    msg_metadata = Column("metadata", JSON, nullable=True)  # tool_calls, thinking, tokens_used, etc. (renamed to avoid SQLAlchemy reserved word)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    conversation = relationship("AssistantConversation", back_populates="messages")

    def __repr__(self):
        return f"<AssistantMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class AssistantSystemEvent(Base):
    """System events for proactive notifications"""
    __tablename__ = "assistant_system_events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    event_type = Column(String(50), nullable=False, index=True)  # 'etl_complete', 'pattern_detected', 'system_alert', etc.
    event_data = Column(JSON, nullable=False)  # Flexible data structure for each event type
    notified = Column(Boolean, server_default=text("FALSE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AssistantSystemEvent(id={self.id}, event_type={self.event_type}, notified={self.notified})>"
