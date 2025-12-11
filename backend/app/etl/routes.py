"""ETL API Routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Body, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from typing import Optional, List

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.etl.models import ETLJob, CandleCoverage, ETLJobLog
from app.etl.schemas import (
    ETLJob as ETLJobSchema,
    ETLJobList,
    ETLJobLog as ETLJobLogSchema,
    ETLJobLogList,
    CoverageSummary,
    CoverageMatrix,
    CoverageMatrixRow,
    CoverageStats,
    TimeframeStats,
    TimeframeCoverage,
    ReprocessRequest,
    DatabaseStatistics,
    CurrentActiveContract,
    ActiveContractHistory,
    ActiveContractPeriod,
    RolloverEvent,
    SymbolDetail,
    SymbolDetailsList,
    CoverageHeatMapResponse,
    CoverageDateRow,
    TimeframeCoverageCell,
    SymbolsList,
    IntegrityCheckResponse,
    IntegrityTimeframeRow,
    IntegrityRelationRow,
    TIMEFRAMES
)

router = APIRouter(prefix="/etl", tags=["ETL"])


# ============================================================================
# File Upload
# ============================================================================

@router.post("/upload-zip", response_model=ETLJobSchema, status_code=status.HTTP_201_CREATED)
async def upload_zip_file(
    file: UploadFile = File(...),
    selected_timeframes: Optional[str] = Form(None),  # JSON string of list
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a Databento ZIP file for processing.

    Args:
        file: ZIP file to upload
        selected_timeframes: JSON string list of timeframes (e.g., '["5min", "1hr"]')
                           If None or empty, processes all 8 timeframes

    Returns:
        ETLJob: Created job with UUID for tracking
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive"
        )

    # Calculate file size
    file_size_mb = file.size / (1024 * 1024) if file.size else None
    file_size_gb = file_size_mb / 1024 if file_size_mb else None

    # Validate file size (max 10GB for large datasets)
    MAX_FILE_SIZE_GB = 10
    if file_size_gb and file_size_gb > MAX_FILE_SIZE_GB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE_GB}GB limit. Got {file_size_gb:.2f}GB"
        )

    # Check if we have the file size (important for disk space checking)
    if not file.size:
        # If size is not available, try to get it
        await file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        await file.seek(0)  # Reset to beginning
        file_size_mb = file_size / (1024 * 1024)
        file_size_gb = file_size_mb / 1024

    # Parse selected timeframes
    import json
    timeframes_list = None
    if selected_timeframes:
        try:
            timeframes_list = json.loads(selected_timeframes)
            # Validate timeframes
            invalid = [tf for tf in timeframes_list if tf not in TIMEFRAMES]
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid timeframes: {invalid}"
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format for selected_timeframes"
            )

    # Create ETL job
    job = ETLJob(
        id=uuid4(),
        user_id=current_user.id,
        zip_filename=file.filename,
        file_size_mb=file_size_mb,
        status="pending",
        selected_timeframes=timeframes_list
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Save uploaded file
    from app.etl.services.file_handler import save_uploaded_file
    try:
        zip_path = await save_uploaded_file(file, job.id)
    except Exception as e:
        # If file save fails, mark job as failed
        job.status = "failed"
        job.error_message = f"Failed to save file: {str(e)}"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Enqueue background task for processing
    from app.etl.worker import get_etl_queue
    from app.etl.tasks import process_etl_job

    try:
        queue = get_etl_queue()
        # Calculate timeout based on file size with generous margin (90 min base, 6 hours max)
        # Formula: 90 min base + 60 min per GB + 50% safety margin = ~3600 sec/GB
        timeout = 5400  # 90 minutes base (for small files)
        if file_size_gb and file_size_gb > 0.5:
            timeout = min(21600, int(5400 + (file_size_gb * 3600)))  # Up to 6 hours
        queue.enqueue(process_etl_job, str(job.id), job_timeout=timeout)
    except Exception as e:
        # If queue fails, mark job as failed
        job.status = "failed"
        job.error_message = f"Failed to enqueue job: {str(e)}"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue job: {str(e)}"
        )

    return job


# ============================================================================
# ZIP Pre-Analysis (FASE 2)
# ============================================================================

@router.post("/analyze-zip")
async def analyze_zip_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pre-analyze a ZIP file without extracting it completely.

    Provides:
    - File count and structure
    - Estimated tick count per file
    - Date ranges and symbols
    - Detection of duplicate data
    - Processing time estimates

    Args:
        file: ZIP file to analyze

    Returns:
        Dictionary with detailed analysis results
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive"
        )

    # Save temporarily for analysis
    import tempfile
    import os

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            # Save uploaded file
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Analyze the ZIP
        from app.etl.services.zip_analyzer import analyze_zip, estimate_processing_time
        from pathlib import Path

        zip_path = Path(tmp_path)
        analysis_result = await analyze_zip(zip_path, db)

        # Add processing time estimates
        if analysis_result["total_estimated_ticks"] > 0:
            time_estimates = await estimate_processing_time(
                analysis_result["total_estimated_ticks"],
                analysis_result["total_csv_files"]
            )
            analysis_result["time_estimates"] = time_estimates

        return analysis_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze ZIP file: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass


# ============================================================================
# Job Management
# ============================================================================

@router.get("/jobs", response_model=ETLJobList)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List ETL jobs with optional filtering"""
    query = select(ETLJob).where(ETLJob.user_id == current_user.id)

    if status_filter:
        query = query.where(ETLJob.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(ETLJob.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return ETLJobList(
        jobs=jobs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/jobs/{job_id}", response_model=ETLJobSchema)
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed status of a specific ETL job"""
    result = await db.execute(
        select(ETLJob).where(
            and_(
                ETLJob.id == job_id,
                ETLJob.user_id == current_user.id
            )
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a running ETL job"""
    result = await db.execute(
        select(ETLJob).where(
            and_(
                ETLJob.id == job_id,
                ETLJob.user_id == current_user.id
            )
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status '{job.status}'"
        )

    job.status = "failed"
    job.error_message = "Cancelled by user"
    job.completed_at = datetime.utcnow()

    await db.commit()


# ============================================================================
# Coverage Endpoints
# ============================================================================

@router.get("/coverage/summary", response_model=CoverageSummary)
async def get_coverage_summary(
    symbol: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get coverage summary showing which days have raw data
    and which days have been populated for each timeframe.
    """
    # TODO: Implement actual query logic
    # For now, return empty structure
    timeframes_dict = {}
    for tf in TIMEFRAMES:
        timeframes_dict[tf] = TimeframeCoverage(
            completed_days=[],
            pending_days=[],
            failed_days=[],
            processing_days=[]
        )

    return CoverageSummary(
        raw_data_days=[],
        timeframes=timeframes_dict
    )


@router.get("/coverage/matrix", response_model=CoverageMatrix)
async def get_coverage_matrix(
    symbol: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get coverage matrix (heatmap data)"""
    # TODO: Implement actual query logic
    return CoverageMatrix(rows=[])


@router.get("/coverage/stats", response_model=CoverageStats)
async def get_coverage_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get coverage statistics"""
    # TODO: Implement actual query logic
    by_timeframe = {}
    for tf in TIMEFRAMES:
        by_timeframe[tf] = TimeframeStats(
            completed=0,
            pending=0,
            failed=0,
            processing=0
        )

    return CoverageStats(
        total_days_with_raw=0,
        by_timeframe=by_timeframe
    )


# ============================================================================
# Reprocess Endpoint
# ============================================================================

@router.post("/reprocess", response_model=ETLJobSchema, status_code=status.HTTP_201_CREATED)
async def reprocess_timeframes(
    request: ReprocessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reprocess specific timeframes for a date range.

    Useful when:
    - Algorithm improvements require recalculation
    - Failed processing needs retry
    - New timeframes added to existing data
    """
    # Validate timeframes
    invalid = [tf for tf in request.timeframes if tf not in TIMEFRAMES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframes: {invalid}"
        )

    # Create reprocess job
    job = ETLJob(
        id=uuid4(),
        user_id=current_user.id,
        zip_filename=f"Reprocess {request.start_date} to {request.end_date}",
        status="pending",
        selected_timeframes=request.timeframes
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # TODO: Queue background reprocess task

    return job


# ============================================================================
# Statistics Endpoint
# ============================================================================

@router.get("/statistics", response_model=DatabaseStatistics)
async def get_database_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall database statistics (simplified for performance).

    Returns basic statistics about the stored market data.
    For performance reasons, counts are limited or approximate.
    """
    from sqlalchemy import text

    stats = {}

    try:
        # 1. Total ticks count - sum from completed ETL jobs (fast)
        tick_count_result = await db.execute(
            text("""
                SELECT COALESCE(SUM(ticks_inserted), 0)
                FROM etl_jobs
                WHERE status = 'completed'
            """)
        )
        stats['total_ticks'] = tick_count_result.scalar() or 0
        has_ticks = stats['total_ticks'] > 0

        # 2. Date range - get from candlestick tables (faster than ticks table)
        try:
            date_range_result = await db.execute(
                text("""
                    SELECT
                        MIN(time_interval)::date as min_date,
                        MAX(time_interval)::date as max_date
                    FROM candlestick_daily
                """)
            )
            date_range_row = date_range_result.fetchone()
            if date_range_row and date_range_row[0]:
                stats['date_range'] = {
                    "min": date_range_row[0],
                    "max": date_range_row[1]
                }
            else:
                stats['date_range'] = None
        except:
            stats['date_range'] = None

        # 3. Unique symbols count - exclude spreads (symbols with "-")
        try:
            symbols_result = await db.execute(
                text("SELECT COUNT(DISTINCT symbol) FROM candlestick_daily WHERE symbol NOT LIKE '%-%'")
            )
            stats['unique_symbols'] = symbols_result.scalar() or 0
        except:
            stats['unique_symbols'] = 0

        # 4. Spread ticks count (disabled for performance)
        stats['spread_ticks'] = 0

        # 5. Rollover periods count (should be small table, safe to count)
        try:
            rollover_result = await db.execute(
                text("SELECT COUNT(*) FROM active_contracts WHERE rollover_period = true")
            )
            stats['rollover_count'] = rollover_result.scalar() or 0
        except:
            stats['rollover_count'] = 0

        # 6. Candles by timeframe - use pg_class for fast approximate counts
        candles_by_timeframe = {}
        timeframes = ['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly']

        for tf in timeframes:
            try:
                table_name = f"candlestick_{tf}"
                count_query = await db.execute(
                    text(f"""
                        SELECT reltuples::bigint
                        FROM pg_class
                        WHERE relname = :table_name
                    """),
                    {"table_name": table_name}
                )
                candles_by_timeframe[tf] = count_query.scalar() or 0
            except:
                candles_by_timeframe[tf] = 0

        return DatabaseStatistics(
            total_ticks=stats['total_ticks'],
            date_range=stats['date_range'],
            unique_symbols=stats['unique_symbols'],
            spread_ticks=stats['spread_ticks'],
            rollover_count=stats['rollover_count'],
            candles_by_timeframe=candles_by_timeframe
        )

    except Exception as e:
        logger.error(f"Error fetching database statistics: {str(e)}")
        # Return empty statistics on error
        return DatabaseStatistics(
            total_ticks=0,
            date_range=None,
            unique_symbols=0,
            spread_ticks=0,
            rollover_count=0,
            candles_by_timeframe={}
        )


# ============================================================================
# Symbol Details Endpoints (FASE 1 - UI Improvements)
# ============================================================================

@router.get("/symbols/list", response_model=SymbolsList)
async def get_symbols_list(
    include_spreads: bool = Query(False, description="Include spread symbols (e.g., NQM4-NQU4)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get simple list of available symbols for dropdowns/filters.

    Returns list of symbols sorted alphabetically.
    """
    from sqlalchemy import text

    try:
        if include_spreads:
            result = await db.execute(
                text("SELECT DISTINCT symbol FROM candlestick_daily ORDER BY symbol")
            )
        else:
            result = await db.execute(
                text("SELECT DISTINCT symbol FROM candlestick_daily WHERE symbol NOT LIKE '%-%' ORDER BY symbol")
            )

        symbols = [row[0] for row in result.fetchall()]

        return SymbolsList(
            symbols=symbols,
            total=len(symbols)
        )
    except Exception as e:
        logger.error(f"Error fetching symbols list: {str(e)}")
        return SymbolsList(symbols=[], total=0)


@router.get("/symbols/details", response_model=SymbolDetailsList)
async def get_symbol_details(
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed statistics for each symbol in the database.

    Returns list of symbols with:
    - Total ticks and candles
    - Available timeframes
    - First/last tick timestamps
    - Days covered and average ticks per day
    """
    from sqlalchemy import text

    symbols = []

    try:
        # Step 1: Get symbols from candlestick_daily (much smaller than ticks)
        logger.info("Starting symbol details query...")

        # Get symbols from daily candles (fast)
        simple_query = await db.execute(
            text("SELECT DISTINCT symbol FROM candlestick_daily WHERE symbol NOT LIKE '%-%' LIMIT 20")
        )
        symbol_list = [row[0] for row in simple_query.fetchall()]
        logger.info(f"Found {len(symbol_list)} distinct symbols: {symbol_list}")

        # Get stats from candlestick_daily (much faster than ticks table)
        symbol_rows = []
        for sym in symbol_list:
            # Get stats from daily candles (fast index scan)
            stats_query = await db.execute(
                text("""
                    SELECT
                        MIN(time_interval) as first_tick,
                        MAX(time_interval) as last_tick,
                        COUNT(*) as days_covered
                    FROM candlestick_daily
                    WHERE symbol = :symbol
                """),
                {"symbol": sym}
            )
            stats_row = stats_query.fetchone()
            if stats_row:
                # Estimate ticks based on candle count (each day ~1M ticks for NQ)
                # We'll get actual ticks from candle counts below
                symbol_rows.append((sym, 0, stats_row[0], stats_row[1], stats_row[2]))

        logger.info(f"Built stats for {len(symbol_rows)} symbols")

        # Pre-fetch candle counts for all symbols in one query per timeframe
        candle_counts = {}  # {symbol: {timeframe: count}}
        for sym in symbol_list:
            candle_counts[sym] = {}

        for tf in TIMEFRAMES:
            try:
                table_name = f"candlestick_{tf}"
                counts_result = await db.execute(
                    text(f"""
                        SELECT symbol, COUNT(*) as cnt
                        FROM {table_name}
                        WHERE symbol = ANY(:symbols)
                        GROUP BY symbol
                    """),
                    {"symbols": symbol_list}
                )
                for row in counts_result.fetchall():
                    if row[0] in candle_counts:
                        candle_counts[row[0]][tf] = row[1]
            except Exception as e:
                logger.debug(f"Error counting {tf}: {e}")
                pass

        # Get total ticks from ETL jobs (real data)
        total_ticks_result = await db.execute(
            text("SELECT COALESCE(SUM(ticks_inserted), 0) FROM etl_jobs WHERE status = 'completed'")
        )
        total_ticks_all = total_ticks_result.scalar() or 0

        # Calculate total 30s candles for proportional distribution
        total_30s_candles = sum(candle_counts.get(sym, {}).get('30s', 0) for sym in symbol_list)

        for row in symbol_rows:
            symbol = row[0]
            first_tick = row[2]
            last_tick = row[3]
            days_covered = row[4] or 1

            # Calculate candles from pre-fetched data
            total_candles = 0
            timeframes_available = []

            symbol_candles = candle_counts.get(symbol, {})
            for tf in TIMEFRAMES:
                count = symbol_candles.get(tf, 0)
                if count > 0:
                    total_candles += count
                    timeframes_available.append(tf)

            # Distribute real ticks proportionally by 30s candles
            candles_30s = symbol_candles.get('30s', 0)
            if total_30s_candles > 0:
                total_ticks = int(total_ticks_all * candles_30s / total_30s_candles)
            else:
                total_ticks = 0
            avg_ticks_per_day = total_ticks // days_covered if days_covered > 0 else 0

            symbols.append(SymbolDetail(
                symbol=symbol,
                total_ticks=total_ticks,
                total_candles=total_candles,
                timeframes_available=timeframes_available,
                first_tick=first_tick,
                last_tick=last_tick,
                days_covered=days_covered,
                avg_ticks_per_day=avg_ticks_per_day
            ))

        return SymbolDetailsList(
            symbols=symbols,
            total=len(symbols)
        )

    except Exception as e:
        import traceback
        logger.error(f"Error fetching symbol details: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return empty list on error instead of crashing
        return SymbolDetailsList(symbols=[], total=0)


@router.get("/coverage", response_model=CoverageHeatMapResponse)
async def get_coverage_heatmap(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get coverage heat map data showing data completeness by date and timeframe.

    Returns matrix of dates x timeframes with status:
    - complete: Has expected number of candles
    - partial: Has some candles but not complete
    - missing: No candles for that date/timeframe
    """
    from sqlalchemy import text
    from datetime import timedelta

    # Expected candles per timeframe for a full trading day (~23 hours)
    expected_candles = {
        '30s': 2760,    # 23 hours * 60 * 2
        '1min': 1380,   # 23 hours * 60
        '5min': 276,    # 23 hours * 12
        '15min': 92,    # 23 hours * 4
        '1hr': 23,      # 23 hours
        '4hr': 6,       # ~6 per day
        'daily': 1,
        'weekly': 1
    }

    coverage_matrix = []
    summary = {"complete": 0, "partial": 0, "missing": 0}

    try:
        # Determine date range from candlestick_daily (fast)
        if start_date is None or end_date is None:
            if symbol:
                date_range_result = await db.execute(
                    text("""
                        SELECT
                            MIN(time_interval)::date as min_date,
                            MAX(time_interval)::date as max_date
                        FROM candlestick_daily
                        WHERE symbol = :symbol
                    """),
                    {"symbol": symbol}
                )
            else:
                date_range_result = await db.execute(
                    text("""
                        SELECT
                            MIN(time_interval)::date as min_date,
                            MAX(time_interval)::date as max_date
                        FROM candlestick_daily
                    """)
                )
            date_row = date_range_result.fetchone()
            if date_row and date_row[0]:
                start_date = date_row[0]
                end_date = date_row[1]
            else:
                return CoverageHeatMapResponse(
                    symbol=symbol,
                    date_range={"start": date.today(), "end": date.today()},
                    coverage_matrix=[],
                    summary=summary
                )

        # Limit date range to avoid too many queries (max 90 days)
        max_days = 90
        if (end_date - start_date).days > max_days:
            start_date = end_date - timedelta(days=max_days)

        # Iterate through each date
        current_date = start_date
        while current_date <= end_date:
            timeframes_coverage = {}

            for tf in TIMEFRAMES:
                table_name = f"candlestick_{tf}"

                try:
                    # Count candles for this date/symbol/timeframe
                    if symbol:
                        count_result = await db.execute(
                            text(f"""
                                SELECT COUNT(*) FROM {table_name}
                                WHERE symbol = :symbol
                                AND DATE(time_interval) = :date
                            """),
                            {"symbol": symbol, "date": current_date}
                        )
                    else:
                        # When no symbol specified, count candles and symbols separately
                        count_result = await db.execute(
                            text(f"""
                                SELECT COUNT(*), COUNT(DISTINCT symbol) FROM {table_name}
                                WHERE DATE(time_interval) = :date
                            """),
                            {"date": current_date}
                        )
                        row = count_result.fetchone()
                        candle_count = row[0] if row else 0
                        num_symbols = row[1] if row else 1

                        # Adjust expected based on number of active symbols
                        expected = expected_candles.get(tf, 100) * max(1, num_symbols)

                        timeframes_coverage[tf] = TimeframeCoverageCell(
                            status="missing" if candle_count == 0 else ("complete" if candle_count >= expected * 0.9 else "partial"),
                            candles=candle_count,
                            expected=expected
                        )

                        # Update summary
                        if candle_count == 0:
                            summary["missing"] += 1
                        elif candle_count >= expected * 0.9:
                            summary["complete"] += 1
                        else:
                            summary["partial"] += 1

                        continue  # Skip the common logic below

                    candle_count = count_result.scalar() or 0
                    expected = expected_candles.get(tf, 100)

                    # Determine status
                    if candle_count == 0:
                        status = "missing"
                        summary["missing"] += 1
                    elif candle_count >= expected * 0.9:  # 90% threshold for complete
                        status = "complete"
                        summary["complete"] += 1
                    else:
                        status = "partial"
                        summary["partial"] += 1

                    timeframes_coverage[tf] = TimeframeCoverageCell(
                        status=status,
                        candles=candle_count,
                        expected=expected
                    )

                except Exception as e:
                    timeframes_coverage[tf] = TimeframeCoverageCell(
                        status="missing",
                        candles=0,
                        expected=expected_candles.get(tf, 100)
                    )
                    summary["missing"] += 1

            coverage_matrix.append(CoverageDateRow(
                date=current_date,
                timeframes=timeframes_coverage
            ))

            current_date += timedelta(days=1)

        return CoverageHeatMapResponse(
            symbol=symbol,
            date_range={"start": start_date, "end": end_date},
            coverage_matrix=coverage_matrix,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Error fetching coverage heatmap: {str(e)}")
        return CoverageHeatMapResponse(
            symbol=symbol,
            date_range={"start": start_date or date.today(), "end": end_date or date.today()},
            coverage_matrix=[],
            summary=summary
        )


# ============================================================================
# Job Logs Endpoints (FASE 2)
# ============================================================================

@router.get("/jobs/{job_id}/logs", response_model=ETLJobLogList)
async def get_job_logs(
    job_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, regex="^(INFO|WARNING|ERROR|DEBUG)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get logs for a specific ETL job with optional filtering.

    Args:
        job_id: UUID of the job
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        level: Optional log level filter (INFO, WARNING, ERROR, DEBUG)

    Returns:
        ETLJobLogList: List of log entries with total count
    """
    # Verify job exists and belongs to user
    job_result = await db.execute(
        select(ETLJob).where(
            and_(
                ETLJob.id == job_id,
                ETLJob.user_id == current_user.id
            )
        )
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Build query for logs
    query = select(ETLJobLog).where(ETLJobLog.job_id == job_id)

    if level:
        query = query.where(ETLJobLog.level == level)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated logs (newest first)
    query = query.order_by(ETLJobLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return ETLJobLogList(
        logs=logs,
        total=total,
        job_id=job_id
    )


# ============================================================================
# Worker Status Endpoint (FASE 2)
# ============================================================================

@router.get("/worker/status")
async def get_worker_status():
    """
    Check RQ worker status and get worker information.

    Returns:
        dict: Worker status including:
            - workers: List of active workers with details
            - total_workers: Count of active workers
            - healthy: Boolean indicating if at least one worker is active
    """
    from app.etl.worker import get_redis_connection
    from rq.worker import Worker

    try:
        redis_conn = get_redis_connection()
        workers = Worker.all(connection=redis_conn)

        workers_info = []
        for w in workers:
            try:
                workers_info.append({
                    "name": w.name,
                    "state": w.get_state(),
                    "current_job": w.get_current_job_id(),
                    "successful_jobs": w.successful_job_count,
                    "failed_jobs": w.failed_job_count,
                    "total_working_time": w.total_working_time,
                    "birth_date": w.birth_date.isoformat() if w.birth_date else None,
                    "last_heartbeat": w.last_heartbeat.isoformat() if hasattr(w, 'last_heartbeat') and w.last_heartbeat else None
                })
            except Exception as e:
                # If one worker fails, continue with others
                workers_info.append({
                    "name": getattr(w, 'name', 'unknown'),
                    "state": "error",
                    "error": str(e)
                })

        return {
            "workers": workers_info,
            "total_workers": len(workers),
            "healthy": len(workers) > 0
        }
    except Exception as e:
        # If we can't connect to Redis or get workers, return unhealthy status
        return {
            "workers": [],
            "total_workers": 0,
            "healthy": False,
            "error": str(e)
        }


# ============================================================================
# Cleanup Endpoint (FASE 2)
# ============================================================================

@router.delete("/jobs/cleanup")
async def cleanup_jobs(
    status_filter: Optional[str] = Query("pending", regex="^(pending|failed|completed|all)$"),
    older_than_hours: int = Query(24, ge=1, le=720),  # Default 24 hours, max 30 days
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cleanup old ETL jobs based on status and age.

    Args:
        status_filter: Status to filter ('pending', 'failed', 'completed', 'all')
        older_than_hours: Delete jobs older than this many hours (default 24, max 720)

    Returns:
        dict: Number of jobs deleted
    """
    from datetime import timedelta

    # Calculate cutoff datetime
    cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

    # Build query
    query = select(ETLJob).where(
        and_(
            ETLJob.user_id == current_user.id,
            ETLJob.created_at < cutoff_time
        )
    )

    if status_filter != "all":
        query = query.where(ETLJob.status == status_filter)

    # Get jobs to delete
    result = await db.execute(query)
    jobs_to_delete = result.scalars().all()

    # Delete jobs (cascade will delete associated logs)
    for job in jobs_to_delete:
        await db.delete(job)

    await db.commit()

    return {
        "deleted_count": len(jobs_to_delete),
        "status_filter": status_filter,
        "older_than_hours": older_than_hours
    }


# ============================================================================
# Active Contracts Endpoints (FASE 2)
# ============================================================================

@router.get("/active-contract", response_model=CurrentActiveContract)
async def get_current_active_contract(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current active contract (front month).

    Returns the contract with the highest trading volume that is currently active.
    The active contract is determined by analyzing daily volume and identifying
    rollover periods.

    Returns:
        CurrentActiveContract: Current active contract with symbol, start_date, and volume metrics

    Raises:
        404: If no active contract is found in the database
    """
    from app.etl.services.active_contract_detector import get_current_active_contract

    result = await get_current_active_contract(db)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active contract found. Please ensure ETL jobs have been processed."
        )

    return CurrentActiveContract(
        symbol=result['symbol'],
        start_date=result['start_date'],
        volume_score=result['volume_score'],
        tick_count=result['tick_count']
    )


@router.get("/active-contract/history", response_model=ActiveContractHistory)
async def get_active_contract_history(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of periods to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical active contract periods.

    Returns a list of active contract periods ordered by most recent first.
    Each period represents a time range when a specific contract was the dominant
    front month contract based on volume analysis.

    Args:
        limit: Maximum number of periods to return (default 10, max 100)

    Returns:
        ActiveContractHistory: List of active contract periods with total count
    """
    from app.etl.services.active_contract_detector import get_rollover_history

    periods = await get_rollover_history(db, limit=limit)

    return ActiveContractHistory(
        periods=[ActiveContractPeriod(**p) for p in periods],
        total=len(periods)
    )


@router.get("/rollover-periods", response_model=List[RolloverEvent])
async def get_rollover_events(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of rollovers to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get rollover events (contract transitions).

    A rollover event occurs when trading volume shifts from one futures contract
    to the next (e.g., from NQM4 to NQU4). This endpoint identifies consecutive
    active contract periods and returns the transition details.

    Args:
        limit: Maximum number of rollover events to return (default 10, max 50)

    Returns:
        List[RolloverEvent]: List of rollover events with from/to symbols, date, and volumes
    """
    from app.etl.services.active_contract_detector import get_rollover_history

    # Get historical periods
    periods = await get_rollover_history(db, limit=limit + 1)

    if len(periods) < 2:
        return []

    # Build rollover events from consecutive periods
    rollover_events = []
    for i in range(len(periods) - 1):
        current_period = periods[i]
        next_period = periods[i + 1]

        # Only create rollover if there's an end_date on the next period
        # (meaning it actually transitioned to the current period)
        if next_period.get('end_date'):
            rollover_events.append(
                RolloverEvent(
                    from_symbol=next_period['symbol'],
                    to_symbol=current_period['symbol'],
                    rollover_date=current_period['start_date'],
                    from_volume=next_period.get('volume_score', 0),
                    to_volume=current_period.get('volume_score', 0)
                )
            )

    return rollover_events[:limit]


# ============================================================================
# Integrity Check Endpoints
# ============================================================================

def get_cme_holidays(year: int) -> list:
    """
    Get CME market holidays for a given year.
    Returns list of dates when the market is closed.
    """
    from datetime import date

    holidays = []

    # New Year's Day (January 1)
    new_year = date(year, 1, 1)
    if new_year.weekday() == 6:  # Sunday
        holidays.append(date(year, 1, 2))  # Observed Monday
    elif new_year.weekday() == 5:  # Saturday
        holidays.append(date(year - 1, 12, 31))  # Observed Friday before
    else:
        holidays.append(new_year)

    # Martin Luther King Jr. Day (3rd Monday of January)
    jan_first = date(year, 1, 1)
    first_monday = jan_first + timedelta(days=(7 - jan_first.weekday()) % 7)
    mlk_day = first_monday + timedelta(weeks=2)
    holidays.append(mlk_day)

    # Presidents' Day (3rd Monday of February)
    feb_first = date(year, 2, 1)
    first_monday = feb_first + timedelta(days=(7 - feb_first.weekday()) % 7)
    presidents_day = first_monday + timedelta(weeks=2)
    holidays.append(presidents_day)

    # Good Friday (varies - simplified calculation)
    # This is a simplified version; actual calculation is complex
    # For 2024: March 29, 2025: April 18
    if year == 2024:
        holidays.append(date(2024, 3, 29))
    elif year == 2025:
        holidays.append(date(2025, 4, 18))

    # Memorial Day (Last Monday of May)
    may_last = date(year, 5, 31)
    memorial_day = may_last - timedelta(days=(may_last.weekday() + 7) % 7)
    holidays.append(memorial_day)

    # Independence Day (July 4)
    july_4 = date(year, 7, 4)
    if july_4.weekday() == 6:  # Sunday
        holidays.append(date(year, 7, 5))  # Observed Monday
    elif july_4.weekday() == 5:  # Saturday
        holidays.append(date(year, 7, 3))  # Observed Friday
    else:
        holidays.append(july_4)

    # Labor Day (1st Monday of September)
    sep_first = date(year, 9, 1)
    labor_day = sep_first + timedelta(days=(7 - sep_first.weekday()) % 7)
    holidays.append(labor_day)

    # Thanksgiving (4th Thursday of November)
    nov_first = date(year, 11, 1)
    first_thursday = nov_first + timedelta(days=(3 - nov_first.weekday() + 7) % 7)
    thanksgiving = first_thursday + timedelta(weeks=3)
    holidays.append(thanksgiving)

    # Christmas (December 25)
    christmas = date(year, 12, 25)
    if christmas.weekday() == 6:  # Sunday
        holidays.append(date(year, 12, 26))  # Observed Monday
    elif christmas.weekday() == 5:  # Saturday
        holidays.append(date(year, 12, 24))  # Observed Friday
    else:
        holidays.append(christmas)

    return holidays


def count_trading_days(start: date, end: date) -> int:
    """
    Count trading days between start and end dates.
    Excludes weekends and market holidays.
    """
    trading_days = 0
    current = start

    # Get holidays for all years in range
    all_holidays = set()
    for year in range(start.year, end.year + 1):
        all_holidays.update(get_cme_holidays(year))

    while current <= end:
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5 and current not in all_holidays:
            trading_days += 1
        current += timedelta(days=1)

    return trading_days


@router.get("/integrity", response_model=IntegrityCheckResponse)
async def check_data_integrity(
    start_date: date = Query(..., description="Start date for integrity check"),
    end_date: date = Query(..., description="End date for integrity check"),
    symbol: Optional[str] = Query(None, description="Symbol to check (optional)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Check data integrity by comparing candle counts across timeframes.

    Verifies mathematical relationships between timeframes:
    - 2 candles of 30s = 1 candle of 1min
    - 5 candles of 1min = 1 candle of 5min
    - etc.

    Returns comparison table with expected vs actual counts.
    """
    from sqlalchemy import text

    # Calculate trading days (excluding weekends and market holidays)
    trading_days = count_trading_days(start_date, end_date)
    total_days = (end_date - start_date).days + 1

    # NQ trades 23 hours per day on trading days
    total_trading_minutes = trading_days * 23 * 60

    # Expected candles per timeframe
    expected_candles = {
        '30s': total_trading_minutes * 2,
        '1min': total_trading_minutes,
        '5min': total_trading_minutes // 5,
        '15min': total_trading_minutes // 15,
        '1hr': total_trading_minutes // 60,
        '4hr': total_trading_minutes // 240,
        'daily': trading_days,
        'weekly': max(1, (total_days + 6) // 7)  # Number of weeks covered
    }

    timeframe_checks = []
    actual_counts = {}
    summary = {"ok": 0, "mismatch": 0, "warning": 0}

    try:
        # Count candles for each timeframe
        for tf in TIMEFRAMES:
            table_name = f"candlestick_{tf}"

            if symbol:
                result = await db.execute(
                    text(f"""
                        SELECT COUNT(*) FROM {table_name}
                        WHERE symbol = :symbol
                        AND DATE(time_interval) BETWEEN :start_date AND :end_date
                    """),
                    {"symbol": symbol, "start_date": start_date, "end_date": end_date}
                )
            else:
                result = await db.execute(
                    text(f"""
                        SELECT COUNT(*) FROM {table_name}
                        WHERE DATE(time_interval) BETWEEN :start_date AND :end_date
                    """),
                    {"start_date": start_date, "end_date": end_date}
                )

            actual = result.scalar() or 0
            expected = expected_candles.get(tf, 0)
            diff = actual - expected
            actual_counts[tf] = actual

            # Determine status based on difference percentage
            if expected == 0:
                status = "ok" if actual == 0 else "warning"
            else:
                diff_pct = abs(diff) / expected * 100
                if diff_pct <= 5:  # Within 5% tolerance
                    status = "ok"
                elif diff_pct <= 15:
                    status = "warning"
                else:
                    status = "mismatch"

            summary[status] += 1

            timeframe_checks.append(IntegrityTimeframeRow(
                timeframe=tf,
                expected=expected,
                actual=actual,
                diff=diff,
                status=status
            ))

        # Check mathematical relationships between timeframes
        relation_checks = []

        # Define relationships: (from_tf, to_tf, expected_ratio)
        relationships = [
            ('30s', '1min', 2.0),
            ('1min', '5min', 5.0),
            ('5min', '15min', 3.0),
            ('15min', '1hr', 4.0),
            ('1hr', '4hr', 4.0),
        ]

        for from_tf, to_tf, expected_ratio in relationships:
            from_count = actual_counts.get(from_tf, 0)
            to_count = actual_counts.get(to_tf, 0)

            if to_count > 0:
                actual_ratio = from_count / to_count
            else:
                actual_ratio = 0.0

            # Check if ratio is within 10% tolerance
            if expected_ratio == 0:
                rel_status = "ok" if actual_ratio == 0 else "mismatch"
            else:
                ratio_diff = abs(actual_ratio - expected_ratio) / expected_ratio * 100
                rel_status = "ok" if ratio_diff <= 10 else "mismatch"

            relation_checks.append(IntegrityRelationRow(
                relation=f"{from_tf}/{to_tf}",
                expected_ratio=expected_ratio,
                actual_ratio=round(actual_ratio, 2),
                status=rel_status
            ))

        # Determine overall status
        if summary["mismatch"] > 0:
            overall_status = "errors"
        elif summary["warning"] > 0:
            overall_status = "warnings"
        else:
            overall_status = "ok"

        return IntegrityCheckResponse(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            total_trading_minutes=total_trading_minutes,
            timeframe_checks=timeframe_checks,
            relation_checks=relation_checks,
            overall_status=overall_status,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Error checking data integrity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking data integrity: {str(e)}"
        )
