"""
WebSocket module for real-time communication.

Provides WebSocket endpoints for 8 channels:
- price: Real-time price updates from CandleEvent
- orderflow: Order flow data (delta, POC) from CandleEvent
- patterns: ICT pattern detection events
- orders: Order status changes
- positions: Position updates
- portfolio: Portfolio snapshot updates
- risk: Risk check events (NEVER throttled - highest priority)
- bot: Bot status events
"""

from .connection_manager import ConnectionManager
from .live import router

__all__ = ['ConnectionManager', 'router']
