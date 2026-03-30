"""
Export Job Model - Tracks dataset export jobs to GCS
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base_class import Base


class ExportJob(Base):
    """
    Tracks export jobs for datasets exported to GCS.

    Lifecycle: queued → running → completed | failed
    """
    __tablename__ = "export_jobs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Request parameters
    timeframe = Column(String(10), nullable=False)  # 30s|1min|5min|15min|1h|4h|1d|1w
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    include_oflow = Column(Boolean, default=False)
    flatten_oflow = Column(Boolean, default=False)

    # Job status
    status = Column(String(20), default="queued")  # queued|running|completed|failed
    progress_pct = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)

    # Estimates
    estimated_rows = Column(Integer, nullable=True)
    estimated_size_mb = Column(Integer, nullable=True)

    # Results (populated when completed)
    files = Column(JSON, nullable=True)  # List of file metadata
    error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # User tracking
    created_by_id = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<ExportJob {self.id} {self.status} {self.timeframe} {self.start_date}-{self.end_date}>"
