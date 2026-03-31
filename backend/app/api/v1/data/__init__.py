"""
Data Platform API module.

REST endpoints for querying historical NQ data from TimescaleDB.
"""

from app.api.v1.data.routes import router

__all__ = ["router"]
