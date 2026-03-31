"""
Bot instance model for trading bot management.

Stores bot configuration, status, and runtime data.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class BotStatus(str, enum.Enum):
    """Bot status enumeration."""
    RUNNING = "RUNNING"
    HALTED = "HALTED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class BotInstance(Base):
    """Bot instance model."""
    __tablename__ = "bot_instances"

    # Primary key
    id = Column(String, primary_key=True)

    # Bot configuration
    name = Column(String, nullable=False)
    strategy_id = Column(String, nullable=False)
    symbol = Column(String, default="NQ")
    timeframe = Column(String, default="5min")

    # Status fields
    status = Column(SQLEnum(BotStatus), default=BotStatus.STOPPED, nullable=False)

    # Kill switch related fields
    halted_at = Column(DateTime, nullable=True)
    halt_reason = Column(String, nullable=True)
    kill_scope = Column(String, nullable=True)  # "per_bot" or "global"

    # Risk configuration (JSONB)
    risk_config = Column(JSON, default={})

    # Trading metrics
    current_pnl = Column(Float, default=0.0)
    consecutive_losses = Column(Integer, default=0)
    account_balance = Column(Float, default=25000.0)  # Apex $25K
    trailing_threshold = Column(Float, default=23000.0)  # $2K trailing

    # Positions and orders (JSON arrays)
    positions = Column(JSON, default=[])
    pending_orders = Column(JSON, default=[])
    recent_orders = Column(JSON, default=[])  # Timestamps of recent orders

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BotInstance {self.id}: {self.name} ({self.status})>"