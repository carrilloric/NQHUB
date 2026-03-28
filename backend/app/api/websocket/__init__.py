"""
WebSocket API Module

Implementation of CONTRACT-005 WebSocket server with FastAPI and Redis bridge.
"""

from .ws_server import router as websocket_router

__all__ = ["websocket_router"]