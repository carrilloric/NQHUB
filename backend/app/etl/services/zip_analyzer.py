"""
ZIP Pre-Analysis Service

Analyzes ZIP file contents without full extraction to provide:
- File count and estimated tick count
- Date ranges and symbols
- Duplicate detection
- Size estimates
"""
import zipfile
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import re
import zstandard as zstd
from io import BytesIO

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.services.csv_parser import extract_symbol_from_filename, extract_date_from_filename, extract_symbol_from_csv_content

logger = logging.getLogger(__name__)


async def analyze_zip(
    zip_path: Path,
    session: AsyncSession
) -> Dict:
    """
    Analyze ZIP file contents without full extraction.

    Args:
        zip_path: Path to the ZIP file
        session: Database session for duplicate checking

    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing ZIP file: {zip_path}")

    analysis_result = {
        "zip_filename": zip_path.name,
        "zip_size_mb": zip_path.stat().st_size / (1024 * 1024),
        "total_files": 0,
        "csv_files": [],
        "date_range": {"start": None, "end": None},
        "symbols": set(),
        "total_estimated_ticks": 0,
        "duplicates_detected": 0,
        "days_already_in_db": [],
        "error": None
    }

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Get list of files
            file_list = zf.filelist
            analysis_result["total_files"] = len(file_list)

            dates = []

            # Log all files in the ZIP for debugging
            logger.info(f"ZIP contains {len(file_list)} files:")
            for idx, fi in enumerate(file_list[:10]):  # Log first 10 files
                logger.info(f"  File {idx+1}: {fi.filename} ({fi.file_size} bytes)")
            if len(file_list) > 10:
                logger.info(f"  ... and {len(file_list) - 10} more files")

            # Check for symbology.csv (GLBX-style files use this)
            symbology_symbols = set()
            for file_info in file_list:
                if file_info.filename.lower() == 'symbology.csv':
                    logger.info("Found symbology.csv - reading symbols...")
                    try:
                        with zf.open(file_info.filename) as f:
                            content = f.read().decode('utf-8')
                            import csv
                            reader = csv.DictReader(content.splitlines())
                            for row in reader:
                                if 'raw_symbol' in row and row['raw_symbol']:
                                    symbology_symbols.add(row['raw_symbol'])
                        logger.info(f"Extracted {len(symbology_symbols)} symbols from symbology.csv")
                    except Exception as e:
                        logger.warning(f"Failed to read symbology.csv: {e}")
                    break

            # Add all symbology symbols to result
            analysis_result["symbols"].update(symbology_symbols)

            for file_info in file_list:
                filename = file_info.filename

                # Skip directories
                if filename.endswith('/'):
                    continue

                # Skip non-CSV files (check both compressed and uncompressed)
                is_csv = (filename.lower().endswith('.csv') or
                         filename.lower().endswith('.csv.zst') or
                         filename.lower().endswith('.csv.gz'))

                if not is_csv:
                    logger.debug(f"Skipping non-CSV file: {filename}")
                    continue

                # Extract metadata from filename
                symbol_from_name = extract_symbol_from_filename(filename)
                file_date = extract_date_from_filename(filename)

                # DUAL VALIDATION: Read symbol from CSV content (authoritative source)
                symbol_from_csv = extract_symbol_from_csv_content(zf, file_info)

                # Use CSV as authority, filename as fallback
                symbol = symbol_from_csv or symbol_from_name

                if symbol:
                    analysis_result["symbols"].add(symbol)

                if file_date:
                    dates.append(file_date)

                # Estimate tick count
                estimated_ticks = 0
                file_size_mb = file_info.file_size / (1024 * 1024)

                if filename.endswith('.csv.zst'):
                    # For compressed files, estimate ~10x compression ratio
                    # Typical CSV line is ~100 bytes, compressed to ~10 bytes
                    estimated_ticks = int(file_info.file_size / 10)
                elif filename.endswith('.csv'):
                    # For uncompressed CSV, sample first 10KB to estimate lines
                    try:
                        with zf.open(file_info.filename) as f:
                            sample = f.read(10240)  # Read 10KB sample
                            lines_in_sample = sample.count(b'\n')
                            if lines_in_sample > 0:
                                bytes_per_line = 10240 / lines_in_sample
                                estimated_ticks = int(file_info.file_size / bytes_per_line) - 1  # -1 for header
                    except Exception as e:
                        logger.warning(f"Could not sample {filename}: {e}")
                        # Fallback: assume ~100 bytes per line
                        estimated_ticks = int(file_info.file_size / 100)

                # Check if data already exists for this date/symbol
                already_exists = False
                if symbol and file_date:
                    already_exists = await check_date_exists(session, symbol, file_date)
                    if already_exists:
                        analysis_result["duplicates_detected"] += 1
                        analysis_result["days_already_in_db"].append({
                            "symbol": symbol,
                            "date": file_date.isoformat()
                        })

                # Add to file list
                file_info_dict = {
                    "filename": filename,
                    "symbol": symbol,
                    "date": file_date.isoformat() if file_date else None,
                    "size_mb": file_size_mb,
                    "estimated_ticks": estimated_ticks,
                    "already_in_db": already_exists,
                    "compressed": filename.endswith('.zst')
                }

                analysis_result["csv_files"].append(file_info_dict)
                analysis_result["total_estimated_ticks"] += estimated_ticks

            # Calculate date range
            if dates:
                analysis_result["date_range"]["start"] = min(dates).isoformat()
                analysis_result["date_range"]["end"] = max(dates).isoformat()

            # Convert set to list for JSON serialization
            analysis_result["symbols"] = sorted(list(analysis_result["symbols"]))

            # Calculate summary stats
            analysis_result["total_days"] = len(set(dates))
            analysis_result["total_csv_files"] = len(analysis_result["csv_files"])

    except Exception as e:
        logger.error(f"Error analyzing ZIP: {e}")
        analysis_result["error"] = str(e)

    return analysis_result


async def check_date_exists(session: AsyncSession, symbol: str, check_date: date) -> bool:
    """
    Check if data already exists for a given symbol and date.

    Args:
        session: Database session
        symbol: Trading symbol
        check_date: Date to check

    Returns:
        True if data exists, False otherwise
    """
    try:
        # Check if we have ticks for this date
        query = text("""
            SELECT EXISTS (
                SELECT 1 FROM market_data_ticks
                WHERE symbol = :symbol
                AND DATE(ts_event) = :date
                LIMIT 1
            )
        """)

        result = await session.execute(query, {
            "symbol": symbol,
            "date": check_date
        })

        exists = result.scalar()
        return bool(exists)

    except Exception as e:
        logger.error(f"Error checking date existence: {e}")
        return False


async def estimate_processing_time(
    total_ticks: int,
    csv_count: int,
    avg_ticks_per_second: int = 10000
) -> Dict[str, float]:
    """
    Estimate processing time based on historical averages.

    Args:
        total_ticks: Total number of ticks to process
        csv_count: Number of CSV files
        avg_ticks_per_second: Average processing speed (default 10k/sec)

    Returns:
        Dictionary with time estimates
    """
    # Base processing time
    tick_processing_seconds = total_ticks / avg_ticks_per_second

    # Add overhead for file operations (2 seconds per file)
    file_overhead_seconds = csv_count * 2

    # Add overhead for candle generation (5% of tick time)
    candle_generation_seconds = tick_processing_seconds * 0.05

    total_seconds = tick_processing_seconds + file_overhead_seconds + candle_generation_seconds

    return {
        "estimated_seconds": total_seconds,
        "estimated_minutes": total_seconds / 60,
        "tick_processing_time": tick_processing_seconds / 60,
        "file_overhead_time": file_overhead_seconds / 60,
        "candle_generation_time": candle_generation_seconds / 60
    }


def generate_file_hash(filename: str, size: int, date: Optional[str]) -> str:
    """
    Generate a hash to identify duplicate files.

    Args:
        filename: Name of the file
        size: File size in bytes
        date: Date string from filename

    Returns:
        MD5 hash string
    """
    unique_str = f"{filename}_{size}_{date}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:16]