"""
File Handler Service

Handles ZIP file uploads and storage for ETL processing.
"""
from pathlib import Path
from uuid import UUID
import logging
import shutil
from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Maximum file size: 10GB (increased for large datasets)
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB in bytes


def check_disk_space(required_bytes: int, path: str = "/tmp") -> None:
    """
    Check if there is enough disk space for the operation.

    Args:
        required_bytes: Number of bytes required
        path: Path to check disk space (default: /tmp)

    Raises:
        HTTPException: If insufficient disk space
    """
    stat = shutil.disk_usage(path)
    available = stat.free

    # Require 3x the file size:
    # - 1x for the ZIP file
    # - 1x for extracted CSV files
    # - 1x for processing overhead and temporary files
    required_with_overhead = required_bytes * 3

    if available < required_with_overhead:
        available_gb = available / (1024**3)
        required_gb = required_with_overhead / (1024**3)
        logger.error(
            f"Insufficient disk space: {available_gb:.2f} GB available, "
            f"{required_gb:.2f} GB required"
        )
        raise HTTPException(
            status_code=507,  # Insufficient Storage
            detail=f"Insufficient disk space. Need {required_gb:.2f} GB, "
                   f"but only {available_gb:.2f} GB available"
        )

    logger.info(
        f"Disk space check passed: {available / (1024**3):.2f} GB available, "
        f"{required_with_overhead / (1024**3):.2f} GB required"
    )


async def save_uploaded_file(file: UploadFile, job_id: UUID) -> Path:
    """
    Save uploaded ZIP file to temporary storage.

    Args:
        file: The uploaded ZIP file from FastAPI
        job_id: UUID of the ETL job for organizing storage

    Returns:
        Path object pointing to the saved file

    Raises:
        HTTPException: If file validation fails
    """
    # Validate file extension
    if not file.filename.endswith('.zip'):
        logger.error(f"Invalid file extension: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected .zip, got {file.filename}"
        )

    # Check file size first (if available)
    if hasattr(file, 'size') and file.size:
        # Quick size check before reading
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is 10GB, got {file.size / (1024**3):.2f}GB"
            )
        # Check disk space before processing
        check_disk_space(file.size, "/tmp")

    # Create job directory
    job_dir = Path(settings.ETL_TEMP_DIR) / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True, mode=0o777)

    # Define file path
    zip_path = job_dir / "uploaded.zip"

    logger.info(f"Saving uploaded file to: {zip_path}")

    # Read and save file with size validation
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    try:
        with open(zip_path, 'wb') as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                file_size += len(chunk)

                # Check size limit
                if file_size > MAX_FILE_SIZE:
                    # Delete partial file
                    zip_path.unlink(missing_ok=True)
                    logger.error(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is 10GB, got {file_size / (1024**3):.2f}GB"
                    )

                f.write(chunk)

        logger.info(f"Successfully saved file: {zip_path} ({file_size / (1024**2):.2f} MB)")
        return zip_path

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up on error
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        logger.error(f"Failed to save file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )


def get_job_directory(job_id: UUID) -> Path:
    """
    Get the working directory for a job.

    Args:
        job_id: UUID of the ETL job

    Returns:
        Path to job directory
    """
    return Path(settings.ETL_TEMP_DIR) / str(job_id)


def cleanup_job_files(job_id: UUID):
    """
    Clean up temporary files for a completed or failed job.

    Args:
        job_id: UUID of the ETL job
    """
    job_dir = get_job_directory(job_id)

    if not job_dir.exists():
        logger.warning(f"Job directory does not exist: {job_dir}")
        return

    try:
        # Remove all files in job directory
        import shutil
        shutil.rmtree(job_dir)
        logger.info(f"Cleaned up job directory: {job_dir}")
    except Exception as e:
        logger.error(f"Failed to cleanup job directory {job_dir}: {str(e)}")
