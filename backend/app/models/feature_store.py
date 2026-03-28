"""
Feature Store Models

SQLAlchemy ORM models for indicators and feature values.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey,
    Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid


class Indicator(Base):
    """Indicators configuration and metadata"""
    __tablename__ = "indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # smc, orderflow, custom
    params = Column(JSONB, server_default='{}')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    feature_values = relationship("FeatureValue", back_populates="indicator", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Indicator {self.name} ({self.type})>"


class FeatureValue(Base):
    """Computed feature values for indicators"""
    __tablename__ = "feature_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id"), nullable=False)
    timeframe = Column(String(10), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    value = Column(JSONB, nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    indicator = relationship("Indicator", back_populates="feature_values")

    __table_args__ = (
        Index('idx_feature_values_indicator_timeframe', 'indicator_id', 'timeframe'),
        Index('idx_feature_values_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<FeatureValue indicator={self.indicator_id} @ {self.timestamp}>"