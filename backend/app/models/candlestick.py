"""
Candlestick Models

SQLAlchemy models for candlestick data across different timeframes.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Candlestick5Min(Base):
    """5-minute candlestick data model"""

    __tablename__ = 'candlestick_5min'

    # Primary key columns
    time_interval = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)

    # Symbol tracking
    is_spread = Column(Boolean, default=False)
    is_rollover_period = Column(Boolean, default=False)

    # OHLCV
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    # Point of Control - Regular
    poc = Column(Float)
    poc_volume = Column(Float)
    poc_percentage = Column(Float)
    poc_location = Column(String)
    poc_position = Column(Float)

    # Point of Control - Real (exact 0.25 tick)
    real_poc = Column(Float)
    real_poc_volume = Column(Float)
    real_poc_percentage = Column(Float)
    real_poc_location = Column(String)

    # Candle structure
    upper_wick = Column(Float)
    lower_wick = Column(Float)
    body = Column(Float)
    wick_ratio = Column(Float)
    rel_uw = Column(Float)
    rel_lw = Column(Float)

    # Volume distribution
    upper_wick_volume = Column(Float)
    lower_wick_volume = Column(Float)
    body_volume = Column(Float)

    # Absorption indicators
    asellers_uwick = Column(Float)
    asellers_lwick = Column(Float)
    abuyers_uwick = Column(Float)
    abuyers_lwick = Column(Float)

    # Order flow
    delta = Column(Float)
    oflow_detail = Column(JSONB)  # Footprint data at 0.25 tick granularity
    oflow_unit = Column(JSONB)     # Footprint data at 1 point granularity

    # Metadata
    tick_count = Column(Integer)

    def __repr__(self):
        return f"<Candlestick5Min(time={self.time_interval}, symbol={self.symbol}, close={self.close})>"
