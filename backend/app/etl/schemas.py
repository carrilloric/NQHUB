"""ETL Schemas"""
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any


# Timeframe constants
TIMEFRAMES = ['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly']


# ============================================================================
# ETL Job Schemas
# ============================================================================

class ETLJobBase(BaseModel):
    zip_filename: str
    file_size_mb: Optional[float] = None
    selected_timeframes: Optional[List[str]] = Field(
        default=None,
        description="List of timeframes to process. If None, processes all 8 timeframes."
    )


class ETLJobCreate(ETLJobBase):
    """Schema for creating a new ETL job"""
    pass


class ETLJobUpdate(BaseModel):
    """Schema for updating ETL job progress"""
    status: Optional[str] = None
    status_detail: Optional[str] = None
    current_step: Optional[int] = None
    progress_pct: Optional[int] = None
    csv_files_found: Optional[int] = None
    csv_files_processed: Optional[int] = None
    ticks_inserted: Optional[int] = None
    candles_created: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class ETLJobInDB(ETLJobBase):
    """Schema for ETL job from database"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[int] = None
    status: str
    status_detail: Optional[str] = None
    total_steps: int
    current_step: int
    progress_pct: int
    csv_files_found: Optional[int] = None
    csv_files_processed: int
    ticks_inserted: int
    candles_created: int
    # Detailed progress fields (FASE 1)
    current_csv_file: Optional[str] = None
    ticks_per_second: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    estimated_completion: Optional[datetime] = None
    # Enhanced progress tracking (FASE 5)
    total_ticks_estimated: Optional[int] = None
    total_days: Optional[int] = None
    days_processed: int = 0
    duplicates_skipped: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    created_at: datetime


class ETLJob(ETLJobInDB):
    """Public ETL job schema"""
    pass


class ETLJobList(BaseModel):
    """Schema for list of ETL jobs"""
    jobs: List[ETLJob]
    total: int
    skip: int
    limit: int


# ============================================================================
# Candle Coverage Schemas
# ============================================================================

class CandleCoverageBase(BaseModel):
    date: date
    symbol: str
    timeframe: str = Field(..., pattern=f"^({'|'.join(TIMEFRAMES)})$")


class CandleCoverageCreate(CandleCoverageBase):
    """Schema for creating candle coverage record"""
    status: str = "pending"


class CandleCoverageUpdate(BaseModel):
    """Schema for updating candle coverage"""
    status: Optional[str] = None
    candles_count: Optional[int] = None
    first_candle: Optional[datetime] = None
    last_candle: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class CandleCoverageInDB(CandleCoverageBase):
    """Schema for candle coverage from database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    candles_count: Optional[int] = None
    first_candle: Optional[datetime] = None
    last_candle: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class CandleCoverage(CandleCoverageInDB):
    """Public candle coverage schema"""
    pass


# ============================================================================
# Coverage Summary Schemas
# ============================================================================

class TimeframeCoverage(BaseModel):
    """Coverage for a single timeframe"""
    completed_days: List[date]
    pending_days: List[date]
    failed_days: List[date]
    processing_days: List[date]


class CoverageSummary(BaseModel):
    """Summary of data coverage"""
    raw_data_days: List[date]
    timeframes: Dict[str, TimeframeCoverage]


class CoverageMatrixRow(BaseModel):
    """Single row in coverage matrix"""
    date: date
    has_raw: bool
    timeframes: Dict[str, Optional[str]]  # timeframe -> status or None


class CoverageMatrix(BaseModel):
    """Coverage matrix for heatmap"""
    rows: List[CoverageMatrixRow]


class TimeframeStats(BaseModel):
    """Statistics for a timeframe"""
    completed: int
    pending: int
    failed: int
    processing: int


class CoverageStats(BaseModel):
    """Overall coverage statistics"""
    total_days_with_raw: int
    by_timeframe: Dict[str, TimeframeStats]


# ============================================================================
# Reprocess Request Schema
# ============================================================================

class ReprocessRequest(BaseModel):
    """Schema for reprocessing request"""
    start_date: date
    end_date: date
    timeframes: List[str] = Field(..., min_items=1)
    symbol: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2024-07-19",
                "end_date": "2024-07-20",
                "timeframes": ["5min", "1hr"],
                "symbol": "NQU4"
            }
        }
    )


# ============================================================================
# Database Statistics Schema
# ============================================================================

class DatabaseStatistics(BaseModel):
    """Database statistics"""
    total_ticks: int
    date_range: Optional[Dict[str, date]] = None  # {"min": date, "max": date}
    unique_symbols: int
    spread_ticks: int
    rollover_count: int
    candles_by_timeframe: Dict[str, int]


# ============================================================================
# Symbol Details Schemas (FASE 1 - UI Improvements)
# ============================================================================

class SymbolDetail(BaseModel):
    """Detailed statistics for a single symbol"""
    symbol: str
    total_ticks: int
    total_candles: int
    timeframes_available: List[str]
    first_tick: Optional[datetime] = None
    last_tick: Optional[datetime] = None
    days_covered: int
    avg_ticks_per_day: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "NQU4",
                "total_ticks": 2358787,
                "total_candles": 45234,
                "timeframes_available": ["30s", "1min", "5min", "15min", "1hr", "4hr", "daily"],
                "first_tick": "2024-06-18T00:00:01.326828Z",
                "last_tick": "2024-07-16T23:59:58.123456Z",
                "days_covered": 29,
                "avg_ticks_per_day": 81337
            }
        }
    )


class SymbolDetailsList(BaseModel):
    """List of symbol details"""
    symbols: List[SymbolDetail]
    total: int


# ============================================================================
# Coverage Matrix Schemas (FASE 1 - Heat Map)
# ============================================================================

class TimeframeCoverageCell(BaseModel):
    """Coverage data for a single timeframe on a single date"""
    status: str  # "complete", "partial", "missing"
    candles: int
    expected: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "complete",
                "candles": 1440,
                "expected": 1440
            }
        }
    )


class CoverageDateRow(BaseModel):
    """Coverage for all timeframes on a single date"""
    date: date
    timeframes: Dict[str, TimeframeCoverageCell]  # timeframe -> coverage data


class CoverageHeatMapResponse(BaseModel):
    """Response for coverage heatmap endpoint"""
    symbol: Optional[str] = None  # None means all symbols
    date_range: Dict[str, date]  # {"start": date, "end": date}
    coverage_matrix: List[CoverageDateRow]
    summary: Dict[str, int]  # {"complete": 45, "partial": 3, "missing": 2}

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "NQU4",
                "date_range": {"start": "2024-06-18", "end": "2024-07-16"},
                "coverage_matrix": [
                    {
                        "date": "2024-06-18",
                        "timeframes": {
                            "30s": {"status": "complete", "candles": 2880, "expected": 2880},
                            "1min": {"status": "complete", "candles": 1440, "expected": 1440},
                            "5min": {"status": "partial", "candles": 200, "expected": 288}
                        }
                    }
                ],
                "summary": {"complete": 45, "partial": 3, "missing": 2}
            }
        }
    )


class CoverageQueryParams(BaseModel):
    """Query parameters for coverage endpoint"""
    symbol: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ============================================================================
# ETL Job Log Schemas (FASE 1)
# ============================================================================

class ETLJobLogBase(BaseModel):
    """Base schema for ETL job logs"""
    level: str = Field(..., pattern="^(INFO|WARNING|ERROR|DEBUG)$")
    message: str
    log_metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class ETLJobLogCreate(ETLJobLogBase):
    """Schema for creating a log entry"""
    job_id: UUID


class ETLJobLogInDB(ETLJobLogBase):
    """Schema for ETL job log from database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: UUID
    created_at: datetime


class ETLJobLog(ETLJobLogInDB):
    """Public ETL job log schema"""
    pass


class ETLJobLogList(BaseModel):
    """Schema for list of ETL job logs"""
    logs: List[ETLJobLog]
    total: int
    job_id: UUID


# ============================================================================
# Active Contracts Schemas (FASE 2)
# ============================================================================

class ActiveContractPeriodBase(BaseModel):
    """Base schema for active contract period"""
    symbol: str = Field(..., max_length=10)
    start_date: date
    end_date: Optional[date] = None
    volume_score: Optional[int] = None
    tick_count: Optional[int] = None
    is_current: bool = False
    rollover_period: bool = False


class ActiveContractPeriodCreate(ActiveContractPeriodBase):
    """Schema for creating an active contract period"""
    pass


class ActiveContractPeriodInDB(ActiveContractPeriodBase):
    """Schema for active contract period from database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ActiveContractPeriod(ActiveContractPeriodInDB):
    """Public active contract period schema"""
    pass


class CurrentActiveContract(BaseModel):
    """Schema for current active contract"""
    symbol: str
    start_date: date
    volume_score: Optional[int] = None
    tick_count: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "NQU4",
                "start_date": "2024-06-18",
                "volume_score": 2358787,
                "tick_count": 2358787
            }
        }
    )


class ActiveContractHistory(BaseModel):
    """Schema for active contract history"""
    periods: List[ActiveContractPeriod]
    total: int


class RolloverEvent(BaseModel):
    """Schema for a rollover event"""
    from_symbol: str
    to_symbol: str
    rollover_date: date
    from_volume: int
    to_volume: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "from_symbol": "NQM4",
                "to_symbol": "NQU4",
                "rollover_date": "2024-06-18",
                "from_volume": 72400,
                "to_volume": 2358787
            }
        }
    )


# ============================================================================
# Symbols List Schemas
# ============================================================================

class SymbolsList(BaseModel):
    """Schema for list of available symbols"""
    symbols: List[str]
    total: int


# ============================================================================
# Integrity Check Schemas
# ============================================================================

class IntegrityTimeframeRow(BaseModel):
    """Schema for integrity check per timeframe"""
    timeframe: str
    expected: int
    actual: int
    diff: int
    status: str  # "ok", "mismatch", "warning"


class IntegrityRelationRow(BaseModel):
    """Schema for integrity relation between timeframes"""
    relation: str  # e.g., "30s/1min"
    expected_ratio: float
    actual_ratio: float
    status: str  # "ok", "mismatch"


class IntegrityCheckResponse(BaseModel):
    """Schema for complete integrity check response"""
    symbol: Optional[str] = None
    start_date: date
    end_date: date
    total_trading_minutes: int
    timeframe_checks: List[IntegrityTimeframeRow]
    relation_checks: List[IntegrityRelationRow]
    overall_status: str  # "ok", "warnings", "errors"
    summary: Dict[str, int]  # {"ok": 5, "mismatch": 2, "warning": 1}
