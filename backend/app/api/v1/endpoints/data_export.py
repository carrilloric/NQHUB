"""
Data Export API Endpoints

Exports candlestick data from TimescaleDB to Google Cloud Storage (GCS) in Parquet format.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.core.database import get_async_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.export_job import ExportJob
from app.workers.export_worker import export_candles_to_gcs, estimate_export_size
from app.etl.worker import get_etl_queue

router = APIRouter()


# ===========================================
# Request/Response Models
# ===========================================

class ExportRequest(BaseModel):
    """Request model for creating an export job"""
    timeframe: str = Field(..., description="Timeframe: 30s|1min|5min|15min|1h|4h|1d|1w")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    include_oflow: bool = Field(default=False, description="Include oflow_detail and oflow_unit columns")
    flatten_oflow: bool = Field(default=False, description="Flatten JSONB to separate columns (if include_oflow=True)")

    class Config:
        json_schema_extra = {
            "example": {
                "timeframe": "1min",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "include_oflow": True,
                "flatten_oflow": False
            }
        }


class FileMetadata(BaseModel):
    """Metadata for an exported file"""
    name: str
    size_mb: float
    gcs_path: str
    signed_url: str
    expires_at: str


class ExportJobResponse(BaseModel):
    """Response model for export job status"""
    job_id: str
    status: str  # queued|running|completed|failed
    progress_pct: int
    current_step: Optional[str] = None
    estimated_rows: Optional[int] = None
    estimated_size_mb: Optional[int] = None
    files: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExportJobCreate(BaseModel):
    """Response after creating an export job"""
    job_id: str
    status: str
    estimated_rows: int
    estimated_size_mb: int


# ===========================================
# API Endpoints
# ===========================================

@router.post("/export", response_model=ExportJobCreate, status_code=status.HTTP_201_CREATED)
async def create_export_job(
    request: ExportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new dataset export job.

    This endpoint creates an async job that will:
    1. Query candles from TimescaleDB
    2. Generate Parquet files (base + optional oflow version)
    3. Upload to Google Cloud Storage
    4. Return signed URLs (valid for 48 hours)

    The job runs in the background via RQ worker.
    Use GET /data/export/{job_id} to check status.
    """
    # Validate timeframe
    valid_timeframes = ["30s", "1min", "5min", "15min", "1h", "4h", "1d", "1w"]
    if request.timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )

    # Estimate export size
    estimated_rows, estimated_size_mb = await estimate_export_size(
        db,
        request.timeframe,
        request.start_date,
        request.end_date
    )

    if estimated_rows == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {request.timeframe} between {request.start_date} and {request.end_date}"
        )

    # Create export job record
    export_job = ExportJob(
        id=uuid.uuid4(),
        timeframe=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date,
        include_oflow=request.include_oflow,
        flatten_oflow=request.flatten_oflow,
        status="queued",
        estimated_rows=estimated_rows,
        estimated_size_mb=estimated_size_mb,
        created_by_id=current_user.id
    )

    db.add(export_job)
    await db.commit()
    await db.refresh(export_job)

    # Queue the job in RQ
    queue = get_etl_queue()
    queue.enqueue(
        export_candles_to_gcs,
        str(export_job.id),
        job_id=str(export_job.id),
        job_timeout='1h',
        result_ttl=86400  # Keep result for 24 hours
    )

    return ExportJobCreate(
        job_id=str(export_job.id),
        status=export_job.status,
        estimated_rows=estimated_rows,
        estimated_size_mb=estimated_size_mb
    )


@router.get("/export/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of an export job.

    Returns job status, progress, and file metadata when completed.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id format. Must be a valid UUID."
        )

    # Fetch job from database
    result = await db.execute(
        select(ExportJob).where(ExportJob.id == job_uuid)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job {job_id} not found"
        )

    # Authorization check: users can only see their own jobs
    # (admins can see all jobs)
    if current_user.role != "admin" and job.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this export job"
        )

    return ExportJobResponse(
        job_id=str(job.id),
        status=job.status,
        progress_pct=job.progress_pct,
        current_step=job.current_step,
        estimated_rows=job.estimated_rows,
        estimated_size_mb=job.estimated_size_mb,
        files=job.files,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.get("/export", response_model=List[ExportJobResponse])
async def list_export_jobs(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    List export jobs for the current user.

    Admins can see all jobs. Regular users only see their own jobs.
    """
    if current_user.role == "admin":
        # Admins see all jobs
        result = await db.execute(
            select(ExportJob)
            .order_by(ExportJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    else:
        # Regular users see only their jobs
        result = await db.execute(
            select(ExportJob)
            .where(ExportJob.created_by_id == current_user.id)
            .order_by(ExportJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

    jobs = result.scalars().all()

    return [
        ExportJobResponse(
            job_id=str(job.id),
            status=job.status,
            progress_pct=job.progress_pct,
            current_step=job.current_step,
            estimated_rows=job.estimated_rows,
            estimated_size_mb=job.estimated_size_mb,
            files=job.files,
            error=job.error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]
