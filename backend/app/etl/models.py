"""
ETL Models
"""
from datetime import datetime, date
from uuid import UUID as UUIDType, uuid4
from sqlalchemy import String, Integer, BigInteger, Float, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from typing import TYPE_CHECKING

from app.db.base_class import Base

# Import User for relationships (must be imported, not TYPE_CHECKING)
from app.models.user import User  # noqa: F401


class ETLJob(Base):
    """ETL Job tracking model"""
    __tablename__ = "etl_jobs"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    zip_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_mb: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # Statuses: pending, extracting, parsing, loading_ticks,
    #           building_candles, detecting_rollovers, completed, failed
    status_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Detailed status message for user (e.g., "Archivo 15/27: 15-JUL-2024")

    # Progress tracking
    total_steps: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Statistics
    csv_files_found: Mapped[int | None] = mapped_column(Integer, nullable=True)
    csv_files_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ticks_inserted: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    candles_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Detailed progress tracking (FASE 1)
    current_csv_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ticks_per_second: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_completion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Enhanced progress tracking (FASE 5)
    total_ticks_estimated: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates_skipped: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Timeframe selection
    selected_timeframes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    logs: Mapped[list["ETLJobLog"]] = relationship("ETLJobLog", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ETLJob(id={self.id}, status='{self.status}', progress={self.progress_pct}%)>"


class ETLJobLog(Base):
    """ETL Job Log model - stores detailed logs for each job"""
    __tablename__ = "etl_job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), ForeignKey("etl_jobs.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message: Mapped[str] = mapped_column(Text, nullable=False)
    log_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)  # Renamed to avoid SQLAlchemy reserved word
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    job: Mapped["ETLJob"] = relationship("ETLJob", foreign_keys=[job_id], back_populates="logs")

    def __repr__(self) -> str:
        return f"<ETLJobLog(job_id={self.job_id}, level='{self.level}', message='{self.message[:50]}...')>"


class CandleCoverage(Base):
    """Candle coverage tracking model"""
    __tablename__ = "candle_coverage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    # Timeframe values: '30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    # Status values: pending, processing, completed, failed

    # Statistics
    candles_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_candle: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_candle: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Processing info
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CandleCoverage(date={self.date}, symbol='{self.symbol}', timeframe='{self.timeframe}', status='{self.status}')>"
