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

    # Order identifiers
    client_order_id = Column(String(100), unique=True, nullable=False)
    broker_order_id = Column(String(100), nullable=True)  # Same as rithmic_order_id
    rithmic_order_id = Column(String(200), nullable=True)  # Legacy, kept for backwards compatibility

    # Bracket order fields
    bracket_role = Column(String(10), nullable=True)  # 'ENTRY' | 'TP' | 'SL' | NULL
    parent_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)

    # Order details
    symbol = Column(String(20), server_default='NQ')
    side = Column(String(10), nullable=False)  # BUY | SELL
    order_type = Column(String(20), nullable=False)  # MARKET | LIMIT | STOP
    type = Column(String(20), nullable=False)  # Legacy, kept for backwards compatibility
    contracts = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)  # Legacy, kept for backwards compatibility
    price = Column(DECIMAL(12, 2), nullable=True)

    # Fill information
    fill_price = Column(DECIMAL(12, 2), nullable=True)
    fill_time = Column(DateTime(timezone=True), nullable=True)

    # P&L tracking
    gross_pnl = Column(DECIMAL(15, 2), nullable=True)
    net_pnl = Column(DECIMAL(15, 2), nullable=True)
    commission = Column(DECIMAL(10, 2), nullable=True)

    # Status tracking
    status = Column(String(50), server_default='PENDING_SUBMIT')  # PENDING_SUBMIT, SUBMITTED, ACCEPTED, FILLED, REJECTED, CANCELLED, FAILED
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)  # Legacy, kept for backwards compatibility
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    bot = relationship("BotInstance", back_populates="orders")
    entry_trades = relationship("Trade", foreign_keys="Trade.entry_order_id", back_populates="entry_order")
    exit_trades = relationship("Trade", foreign_keys="Trade.exit_order_id", back_populates="exit_order")
    parent_order = relationship("Order", remote_side=[id], foreign_keys=[parent_order_id])

    __table_args__ = (
        Index('idx_orders_bot', 'bot_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_submitted', 'submitted_at'),
        Index('idx_orders_rithmic', 'rithmic_order_id'),
        Index('idx_orders_client_order_id', 'client_order_id'),
        Index('idx_orders_broker_order_id', 'broker_order_id'),
        Index('idx_orders_bracket_role', 'bracket_role'),
        Index('idx_orders_parent_order_id', 'parent_order_id'),
    )

    def __repr__(self):
        role_str = f" ({self.bracket_role})" if self.bracket_role else ""
        return f"<Order {self.side} {self.contracts}x @ {self.price} ({self.status}){role_str}>"


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