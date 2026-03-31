"""
Research & Backtesting API Module (AUT-363)

Provides REST API for backtest execution, optimization, and strategy management.
"""
from app.api.v1.research.routes import router

__all__ = ["router"]
