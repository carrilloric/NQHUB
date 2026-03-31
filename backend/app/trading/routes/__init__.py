"""
Trading Routes

REST API endpoints for trading module.
"""
from app.trading.routes.risk import router as risk_router

__all__ = ["risk_router"]
