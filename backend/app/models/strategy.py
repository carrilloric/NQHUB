"""
Strategy & Backtesting Models

SQLAlchemy ORM models for strategies, backtesting runs, and approvals.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, Text,
    Index, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid


class Strategy(Base):
    """Trading strategies definition and metadata"""
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    version = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)  # rule_based, ml, rl, hybrid
    source_code = Column(Text, nullable=True)
    required_features = Column(JSONB, server_default='[]')
    model_id = Column(String(200), nullable=True)  # HuggingFace model ID (ML/RL only)
    status = Column(String(50), server_default='draft')  # draft, approved, deprecated
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    backtest_runs = relationship("BacktestRun", back_populates="strategy", cascade="all, delete-orphan")
    approvals = relationship("StrategyApproval", back_populates="strategy", cascade="all, delete-orphan")
    bot_instances = relationship("BotInstance", back_populates="strategy")

    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_strategy_name_version'),
        Index('idx_strategies_status', 'status'),
        Index('idx_strategies_type', 'type'),
    )

    def __repr__(self):
        return f"<Strategy {self.name} v{self.version} ({self.type})>"


class BacktestRun(Base):
    """Backtesting run records with configuration and results"""
    __tablename__ = "backtest_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    params = Column(JSONB, nullable=False)
    config = Column(JSONB, nullable=False)  # dates, commission, slippage, tp, sl
    results = Column(JSONB, nullable=True)  # metrics: sharpe, sortino, dd, etc.
    source = Column(String(50), server_default='nqhub')  # nqhub | notebook
    status = Column(String(50), server_default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="backtest_runs")
    approvals = relationship("StrategyApproval", back_populates="backtest_run")

    __table_args__ = (
        Index('idx_backtest_runs_strategy', 'strategy_id'),
        Index('idx_backtest_runs_status', 'status'),
        Index('idx_backtest_runs_created', 'created_at'),
    )

    def __repr__(self):
        return f"<BacktestRun strategy={self.strategy_id} status={self.status}>"


class StrategyApproval(Base):
    """Strategy approval records for production deployment"""
    __tablename__ = "strategy_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    backtest_run_id = Column(UUID(as_uuid=True), ForeignKey("backtest_runs.id"), nullable=False)
    approved_params = Column(JSONB, nullable=False)
    approved_by = Column(String(200), nullable=True)
    approved_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="approvals")
    backtest_run = relationship("BacktestRun", back_populates="approvals")
    bot_instances = relationship("BotInstance", back_populates="approval")

    __table_args__ = (
        Index('idx_approvals_strategy', 'strategy_id'),
        Index('idx_approvals_approved_at', 'approved_at'),
    )

    def __repr__(self):
        return f"<StrategyApproval strategy={self.strategy_id} by={self.approved_by}>"