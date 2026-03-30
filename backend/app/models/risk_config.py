"""
Risk & Configuration Models

SQLAlchemy ORM models for risk management, trading accounts, and schedules.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean,
    Index, func, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid


class RiskConfig(Base):
    """Risk configuration for bot instances"""
    __tablename__ = "risk_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bot_instances.id"), nullable=False)
    max_daily_loss_usd = Column(DECIMAL(10, 2), nullable=False)
    max_trailing_drawdown_usd = Column(DECIMAL(10, 2), nullable=False)
    max_contracts = Column(Integer, server_default='1')
    max_orders_per_minute = Column(Integer, server_default='10')
    news_blackout_minutes = Column(Integer, server_default='5')
    apex_consistency_pct = Column(DECIMAL(5, 2), server_default='30.0')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    bot = relationship("BotInstance", back_populates="risk_limits")

    __table_args__ = (
        Index('idx_risk_config_bot', 'bot_id'),
    )

    def __repr__(self):
        return f"<RiskConfig bot={self.bot_id} max_loss={self.max_daily_loss_usd}>"


class ApexAccount(Base):
    """Apex trading accounts configuration"""
    __tablename__ = "apex_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name = Column(String(200), nullable=False)
    account_size_usd = Column(DECIMAL(12, 2), nullable=False)
    trailing_threshold_usd = Column(DECIMAL(10, 2), nullable=False)
    daily_loss_limit_usd = Column(DECIMAL(10, 2), nullable=False)
    rithmic_credentials = Column(JSONB, nullable=True)  # encrypted
    is_active = Column(Boolean, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bot_instances = relationship("BotInstance", back_populates="apex_account")

    __table_args__ = (
        Index('idx_apex_accounts_name', 'account_name'),
        Index('idx_apex_accounts_active', 'is_active'),
    )

    def __repr__(self):
        return f"<ApexAccount {self.account_name} size={self.account_size_usd}>"


class TradingSchedule(Base):
    """Trading schedules for automated trading sessions"""
    __tablename__ = "trading_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    timezone = Column(String(50), server_default='America/New_York')
    sessions = Column(JSONB, nullable=False)  # [{start: "08:00", end: "16:00", days: [1,2,3,4,5]}]
    is_active = Column(Boolean, server_default='true')

    __table_args__ = (
        Index('idx_trading_schedules_name', 'name'),
        Index('idx_trading_schedules_active', 'is_active'),
    )

    def __repr__(self):
        return f"<TradingSchedule {self.name} ({self.timezone})>"