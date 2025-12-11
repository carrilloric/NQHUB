"""
ETL Job Logger

Dual logging system that writes to both:
1. Database (etl_job_logs table) for UI display
2. Python logging for server-side debugging
"""
import logging
from uuid import UUID
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.models import ETLJobLog


class ETLJobLogger:
    """
    Logger for ETL jobs that writes to both database and file logs.

    Usage:
        logger = ETLJobLogger(job_id, session)
        logger.info("Processing started", file_count=15)
        logger.warning("Potential data gap detected", gap_size=100)
        logger.error("Failed to parse CSV", filename="data.csv", error=str(e))
    """

    def __init__(self, job_id: UUID, session: AsyncSession):
        """
        Initialize the logger.

        Args:
            job_id: UUID of the ETL job
            session: Async database session
        """
        self.job_id = job_id
        self.session = session
        self.file_logger = logging.getLogger(f"etl.job.{job_id}")

    async def info(self, message: str, **metadata: Any) -> None:
        """
        Log an INFO level message.

        Args:
            message: Log message
            **metadata: Additional context as key-value pairs
        """
        self.file_logger.info(f"[{self.job_id}] {message} {metadata if metadata else ''}")
        await self._write_to_db("INFO", message, metadata or {})

    async def warning(self, message: str, **metadata: Any) -> None:
        """
        Log a WARNING level message.

        Args:
            message: Log message
            **metadata: Additional context as key-value pairs
        """
        self.file_logger.warning(f"[{self.job_id}] {message} {metadata if metadata else ''}")
        await self._write_to_db("WARNING", message, metadata or {})

    async def error(self, message: str, **metadata: Any) -> None:
        """
        Log an ERROR level message.

        Args:
            message: Log message
            **metadata: Additional context as key-value pairs
        """
        self.file_logger.error(f"[{self.job_id}] {message} {metadata if metadata else ''}")
        await self._write_to_db("ERROR", message, metadata or {})

    async def debug(self, message: str, **metadata: Any) -> None:
        """
        Log a DEBUG level message.

        Args:
            message: Log message
            **metadata: Additional context as key-value pairs
        """
        self.file_logger.debug(f"[{self.job_id}] {message} {metadata if metadata else ''}")
        await self._write_to_db("DEBUG", message, metadata or {})

    async def _write_to_db(self, level: str, message: str, metadata: Dict[str, Any]) -> None:
        """
        Write log entry to database.

        Args:
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            message: Log message
            metadata: Additional context as dictionary
        """
        try:
            log_entry = ETLJobLog(
                job_id=self.job_id,
                level=level,
                message=message,
                log_metadata=metadata or None,
                created_at=datetime.utcnow()
            )
            self.session.add(log_entry)
            await self.session.commit()
        except Exception as e:
            # Don't let logging failures crash the ETL job
            self.file_logger.exception(f"Failed to write log to database: {e}")
            # Try to rollback to keep session usable
            try:
                await self.session.rollback()
            except Exception:
                pass
