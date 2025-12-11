"""
Extractor Service

Handles ZIP extraction and .zst decompression for ETL processing.
"""
from pathlib import Path
from typing import List
from uuid import UUID
import zipfile
import logging
import zstandard as zstd
from app.config import settings

logger = logging.getLogger(__name__)


def extract_zip(zip_path: Path, job_id: UUID) -> List[Path]:
    """
    Extract ZIP file and decompress any .zst files inside.

    Args:
        zip_path: Path to the uploaded ZIP file
        job_id: UUID of the ETL job

    Returns:
        List of Path objects pointing to extracted CSV files

    Raises:
        Exception: If extraction or decompression fails
    """
    # Create extraction directory
    extract_dir = Path(settings.ETL_TEMP_DIR) / str(job_id) / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True, mode=0o777)

    logger.info(f"Extracting ZIP file: {zip_path} to {extract_dir}")

    try:
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = zip_ref.namelist()
            logger.info(f"Extracted {len(extracted_files)} files from ZIP")

        # Find all .csv.zst files
        zst_files = list(extract_dir.rglob("*.csv.zst"))
        logger.info(f"Found {len(zst_files)} .csv.zst files to decompress")

        csv_files = []

        # Decompress each .zst file
        for zst_file in zst_files:
            try:
                csv_file = decompress_zst_file(zst_file)
                csv_files.append(csv_file)

                # Delete .zst file after successful decompression
                zst_file.unlink()
                logger.info(f"Deleted compressed file: {zst_file}")

            except Exception as e:
                logger.error(f"Failed to decompress {zst_file}: {str(e)}")
                raise

        # Also find any CSV files that were already uncompressed in the ZIP
        existing_csv_files = list(extract_dir.rglob("*.csv"))
        # Filter out the ones we just created
        existing_csv_files = [f for f in existing_csv_files if f not in csv_files]

        if existing_csv_files:
            logger.info(f"Found {len(existing_csv_files)} existing CSV files (not compressed)")
            csv_files.extend(existing_csv_files)

        logger.info(f"Successfully extracted and decompressed {len(csv_files)} CSV files")
        return csv_files

    except zipfile.BadZipFile as e:
        logger.error(f"Invalid ZIP file: {zip_path}")
        raise Exception(f"Invalid ZIP file: {str(e)}")
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise


def decompress_zst_file(zst_path: Path) -> Path:
    """
    Decompress a single .zst file using zstandard.

    Args:
        zst_path: Path to the .zst file

    Returns:
        Path to the decompressed CSV file

    Raises:
        Exception: If decompression fails
    """
    # Output path: remove .zst extension
    csv_path = zst_path.with_suffix('')

    logger.info(f"Decompressing: {zst_path.name} -> {csv_path.name}")

    try:
        # Get file size for logging
        zst_size = zst_path.stat().st_size
        logger.info(f"Compressed size: {zst_size / (1024**2):.2f} MB")

        # Decompress using zstandard
        dctx = zstd.ZstdDecompressor()

        with open(zst_path, 'rb') as f_in:
            with open(csv_path, 'wb') as f_out:
                dctx.copy_stream(f_in, f_out)

        # Log decompressed size
        csv_size = csv_path.stat().st_size
        logger.info(f"Decompressed size: {csv_size / (1024**2):.2f} MB")
        logger.info(f"Compression ratio: {zst_size / csv_size:.2%}")

        return csv_path

    except Exception as e:
        # Clean up partial output file
        if csv_path.exists():
            csv_path.unlink(missing_ok=True)
        logger.error(f"Decompression failed: {str(e)}")
        raise Exception(f"Failed to decompress {zst_path.name}: {str(e)}")


def get_extracted_directory(job_id: UUID) -> Path:
    """
    Get the extraction directory for a job.

    Args:
        job_id: UUID of the ETL job

    Returns:
        Path to extraction directory
    """
    return Path(settings.ETL_TEMP_DIR) / str(job_id) / "extracted"
