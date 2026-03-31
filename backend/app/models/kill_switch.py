"""
Kill switch event model for audit logging.

Records all kill switch activations for compliance and analysis.
"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class KillSwitchEventModel(Base):
    """Kill switch event model for audit trail."""
    __tablename__ = "kill_switch_events"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Event details
    bot_id = Column(String, nullable=True)  # Null for global events
    scope = Column(String, nullable=False)  # "per_bot" or "global"
    reason = Column(String, nullable=False)

    # Trigger information
    triggered_by = Column(String, nullable=False)  # "manual" or "circuit_breaker"
    circuit_breaker_type = Column(String, nullable=True)  # Type if triggered by circuit breaker

    # Impact metrics
    positions_closed = Column(Integer, default=0)
    orders_cancelled = Column(Integer, default=0)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KillSwitchEvent {self.id}: {self.scope} for {self.bot_id or 'ALL'}>"