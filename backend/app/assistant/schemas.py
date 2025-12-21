"""
Pydantic schemas for AI Assistant API
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, Any
from datetime import datetime
from uuid import UUID


# ============== Message Schemas ==============

class MessageBase(BaseModel):
    """Base schema for messages"""
    role: Literal["user", "assistant", "system"]
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    pass


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: UUID
    conversation_id: UUID
    metadata: Optional[dict[str, Any]] = Field(None, alias="msg_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============== Conversation Schemas ==============

class ConversationBase(BaseModel):
    """Base schema for conversations"""
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationListItem(BaseModel):
    """Schema for conversation list item (without messages)"""
    id: UUID
    user_id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Chat Request/Response ==============

class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[UUID] = None  # If None, create new conversation


class ChatResponse(BaseModel):
    """Schema for chat response"""
    conversation_id: UUID
    user_message: MessageResponse
    assistant_message: MessageResponse
    metadata: Optional[dict[str, Any]] = None  # tool_used, thinking, etc.


# ============== System Events ==============

class SystemEventType(str):
    """Event types for system notifications"""
    ETL_COMPLETE = "etl_complete"
    ETL_FAILED = "etl_failed"
    PATTERN_DETECTED = "pattern_detected"
    DATABASE_STATS = "database_stats"
    SYSTEM_ALERT = "system_alert"
    WORKER_STATUS = "worker_status"


class SystemEventResponse(BaseModel):
    """Schema for system event response"""
    id: UUID
    event_type: str
    event_data: dict[str, Any]
    notified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarkEventsReadRequest(BaseModel):
    """Schema for marking events as read"""
    event_ids: list[UUID]


# ============== Status Schemas ==============

class ETLStatusResponse(BaseModel):
    """Schema for ETL status"""
    total_jobs: int
    running: int
    completed: int
    failed: int
    recent_jobs: list[dict[str, Any]]


class PatternStatusResponse(BaseModel):
    """Schema for pattern detection status"""
    total_fvgs: int
    total_lps: int
    total_obs: int
    recent_detections: list[dict[str, Any]]


class DatabaseStatsResponse(BaseModel):
    """Schema for database statistics"""
    total_candles: int
    total_ticks: int
    active_contracts: int
    coverage_summary: dict[str, Any]


class SystemHealthResponse(BaseModel):
    """Schema for system health"""
    api_status: str
    database_status: str
    redis_status: str
    workers_active: int
    workers_total: int
    memory_usage: Optional[dict[str, Any]] = None


# ============== Vanna Training ==============

class VannaTrainingCreate(BaseModel):
    """Schema for creating Vanna training data"""
    question: str
    sql_query: str
    was_successful: bool = True
    feedback_score: Optional[int] = Field(None, ge=1, le=5)


class VannaTrainingResponse(BaseModel):
    """Schema for Vanna training response"""
    id: UUID
    question: str
    sql_query: str
    was_successful: bool
    feedback_score: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Feedback ==============

class FeedbackRequest(BaseModel):
    """Schema for user feedback on SQL queries"""
    message_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
