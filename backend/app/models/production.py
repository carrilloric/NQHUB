"""
Production Models

SQLAlchemy ORM models for bot instances, orders, trades, and production monitoring.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, Text, Boolean,
    Index, func, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid


class BotInstance(Base):
    """Bot instances for live and paper trading"""
    __tablename__ = "bot_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("strategy_approvals.id"), nullable=True)
    apex_account_id = Column(UUID(as_uuid=True), ForeignKey("apex_accounts.id"), nullable=True)
    mode = Column(String(50), server_default='paper')  # paper | live
    status = Column(String(50), server_default='stopped')  # stopped, running, error, killed
    approved_params = Column(JSONB, nullable=True)
    active_params = Column(JSONB, nullable=True)
    params_modified = Column(Boolean, server_default='false')
    risk_config = Column(JSONB, nullable=True)  # Alert notification config
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    strategy = relationship("Strategy", back_populates="bot_instances")
    approval = relationship("StrategyApproval", back_populates="bot_instances")
    apex_account = relationship("ApexAccount", back_populates="bot_instances")
    state_logs = relationship("BotStateLog", back_populates="bot", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="bot", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="bot", cascade="all, delete-orphan")
    risk_limits = relationship("RiskConfig", back_populates="bot", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_bot_instances_status', 'status'),
        Index('idx_bot_instances_mode', 'mode'),
        Index('idx_bot_instances_strategy', 'strategy_id'),
    )

    def __repr__(self):
        return f"<BotInstance {self.name} ({self.mode}/{self.status})>"


class BotStateLog(Base):
    """Bot state change history"""
    __tablename__ = "bot_state_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instances.id"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bot = relationship("BotInstance", back_populates="state_logs")

    __table_args__ = (
        Index('idx_bot_state_log_bot', 'bot_id'),
        Index('idx_bot_state_log_created', 'created_at'),
    )

    def __repr__(self):
        return f"<BotStateLog bot={self.bot_id} {self.from_status}->{self.to_status}>"


class Order(Base):
    """Trading orders executed by bots"""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instances.id"), nullable=False)
    rithmic_order_id = Column(String(200), nullable=True)
    symbol = Column(String(20), server_default='NQ')
    side = Column(String(10), nullable=False)  # BUY | SELL
    type = Column(String(20), nullable=False)  # MARKET | LIMIT | STOP
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(12, 2), nullable=True)
    fill_price = Column(DECIMAL(12, 2), nullable=True)
    status = Column(String(50), server_default='PENDING')
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    bot = relationship("BotInstance", back_populates="orders")
    entry_trades = relationship("Trade", foreign_keys="Trade.entry_order_id", back_populates="entry_order")
    exit_trades = relationship("Trade", foreign_keys="Trade.exit_order_id", back_populates="exit_order")

    __table_args__ = (
        Index('idx_orders_bot', 'bot_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_submitted', 'submitted_at'),
        Index('idx_orders_rithmic', 'rithmic_order_id'),
    )

    def __repr__(self):
        return f"<Order {self.side} {self.quantity}x @ {self.price} ({self.status})>"


class Trade(Base):
    """Completed trades with entry and exit orders"""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instances.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    entry_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    exit_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    direction = Column(String(10), nullable=True)  # LONG | SHORT
    entry_price = Column(DECIMAL(12, 2), nullable=True)
    exit_price = Column(DECIMAL(12, 2), nullable=True)
    quantity = Column(Integer, nullable=True)
    pnl_ticks = Column(Integer, nullable=True)
    pnl_usd = Column(DECIMAL(12, 2), nullable=True)
    commission = Column(DECIMAL(8, 2), nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, server_default='[]')
    opened_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    bot = relationship("BotInstance", back_populates="trades")
    strategy = relationship("Strategy")
    entry_order = relationship("Order", foreign_keys=[entry_order_id], back_populates="entry_trades")
    exit_order = relationship("Order", foreign_keys=[exit_order_id], back_populates="exit_trades")

    __table_args__ = (
        Index('idx_trades_bot', 'bot_id'),
        Index('idx_trades_strategy', 'strategy_id'),
        Index('idx_trades_opened', 'opened_at'),
        Index('idx_trades_closed', 'closed_at'),
    )

    def __repr__(self):
        return f"<Trade {self.direction} {self.quantity}x P&L={self.pnl_usd}>"