"""
Event Bus schemas for NQHUB trading system.

This module defines the JSON contract between the backend trading engine
and the frontend via Redis pub/sub.

All events inherit from BaseEvent and include:
- channel: Redis pub/sub channel name
- ts: Timestamp in UTC
- bot_id: Trading bot identifier

Events are used by:
- WsBridgeActor: Publishes events to Redis for WebSocket consumption
- DbWriterActor: Persists events to PostgreSQL
- Frontend: Receives events via WebSocket

NQ Futures constants:
- tick_size = 0.25
- tick_value = $5.00
- point_value = $20.00
"""
from app.trading.events.schemas import (
    BaseEvent,
    CandleEvent,
    PatternEvent,
    RiskCheckEvent,
    KillSwitchEvent,
    OrderEvent,
    PositionEvent,
    NQ_TICK_SIZE,
    NQ_TICK_VALUE,
    NQ_POINT_VALUE,
)

__all__ = [
    'BaseEvent',
    'CandleEvent',
    'PatternEvent',
    'RiskCheckEvent',
    'KillSwitchEvent',
    'OrderEvent',
    'PositionEvent',
    'NQ_TICK_SIZE',
    'NQ_TICK_VALUE',
    'NQ_POINT_VALUE',
]
