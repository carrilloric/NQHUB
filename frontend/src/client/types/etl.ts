/**
 * ETL Types
 * TypeScript interfaces matching backend schemas
 */

// Timeframe constants
export const TIMEFRAMES = ['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'] as const;
export type Timeframe = typeof TIMEFRAMES[number];

// Job status types
export const JOB_STATUSES = [
  'pending',
  'extracting',
  'parsing',
  'loading_ticks',
  'building_candles',
  'detecting_rollovers',
  'finalizing',
  'completed',
  'failed'
] as const;
export type JobStatus = typeof JOB_STATUSES[number];

// ETL Job interface matching backend schema
export interface ETLJob {
  id: string;
  user_id?: number;
  zip_filename: string;
  file_size_mb?: number;
  status: JobStatus;
  status_detail?: string | null; // Human-readable detailed status (e.g., "Archivo 15/27: 15-JUL-2024")
  total_steps: number;
  current_step: number;
  progress_pct: number;
  selected_timeframes?: Timeframe[] | null;
  csv_files_found?: number | null;
  csv_files_processed: number;
  ticks_inserted: number;
  candles_created: number;
  // Detailed progress fields (FASE 1)
  current_csv_file?: string | null;
  ticks_per_second?: number | null;
  memory_usage_mb?: number | null;
  estimated_completion?: string | null;
  // Enhanced progress tracking (FASE 5)
  total_ticks_estimated?: number | null;
  total_days?: number | null;
  days_processed: number;
  duplicates_skipped: number;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  error_details?: Record<string, any> | null;
  created_at: string;
}

// ETL Job List response
export interface ETLJobList {
  jobs: ETLJob[];
  total: number;
  skip: number;
  limit: number;
}

// Upload request
export interface UploadZipRequest {
  file: File;
  selected_timeframes?: Timeframe[];
}

// Status badge color mapping
export const STATUS_COLORS: Record<JobStatus, string> = {
  pending: 'bg-gray-500/20 text-gray-700 dark:text-gray-300',
  extracting: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  parsing: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  loading_ticks: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  building_candles: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  detecting_rollovers: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  finalizing: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  completed: 'bg-green-500/20 text-green-700 dark:text-green-300',
  failed: 'bg-red-500/20 text-red-700 dark:text-red-300',
};

// Status display labels
export const STATUS_LABELS: Record<JobStatus, string> = {
  pending: 'Pending',
  extracting: 'Extracting',
  parsing: 'Parsing',
  loading_ticks: 'Loading Ticks',
  building_candles: 'Building Candles',
  detecting_rollovers: 'Detecting Rollovers',
  finalizing: 'Finalizing',
  completed: 'Completed',
  failed: 'Failed',
};

// Helper to check if job is active (should be polled)
export function isJobActive(status: JobStatus): boolean {
  return ['pending', 'extracting', 'parsing', 'loading_ticks', 'building_candles', 'detecting_rollovers', 'finalizing'].includes(status);
}

// Helper to check if job is terminal (no longer processing)
export function isJobTerminal(status: JobStatus): boolean {
  return ['completed', 'failed'].includes(status);
}


// ============================================================================
// ETL Job Log Types (FASE 3)
// ============================================================================

export type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';

export interface ETLJobLog {
  id: number;
  job_id: string;
  level: LogLevel;
  message: string;
  metadata?: Record<string, any> | null;
  created_at: string;
}

export interface ETLJobLogList {
  logs: ETLJobLog[];
  total: number;
  job_id: string;
}

// Log level colors for UI
export const LOG_LEVEL_COLORS: Record<LogLevel, string> = {
  INFO: 'text-blue-600 dark:text-blue-400',
  WARNING: 'text-yellow-600 dark:text-yellow-400',
  ERROR: 'text-red-600 dark:text-red-400',
  DEBUG: 'text-gray-600 dark:text-gray-400',
};

// Log level background colors
export const LOG_LEVEL_BG_COLORS: Record<LogLevel, string> = {
  INFO: 'bg-blue-50 dark:bg-blue-950/30',
  WARNING: 'bg-yellow-50 dark:bg-yellow-950/30',
  ERROR: 'bg-red-50 dark:bg-red-950/30',
  DEBUG: 'bg-gray-50 dark:bg-gray-950/30',
};


// ============================================================================
// Database Statistics Types
// ============================================================================

export interface DatabaseStatistics {
  total_ticks: number;
  date_range: {
    min: string;
    max: string;
  } | null;
  unique_symbols: number;
  spread_ticks: number;
  rollover_count: number;
  candles_by_timeframe: Record<string, number>;
}

// ============================================================================
// Worker Status Types (FASE 5)
// ============================================================================

export interface WorkerInfo {
  name: string;
  state: string;
  current_job?: string | null;
  successful_jobs: number;
  failed_jobs: number;
  total_working_time: number;
  birth_date?: string | null;
  last_heartbeat?: string | null;
  error?: string;
}

export interface WorkerStatus {
  workers: WorkerInfo[];
  total_workers: number;
  healthy: boolean;
  error?: string;
}

// ============================================================================
// Symbol Details Types (FASE 1 - UI Improvements)
// ============================================================================

export interface SymbolDetail {
  symbol: string;
  total_ticks: number;
  total_candles: number;
  timeframes_available: string[];
  first_tick: string | null;
  last_tick: string | null;
  days_covered: number;
  avg_ticks_per_day: number;
}

export interface SymbolDetailsList {
  symbols: SymbolDetail[];
  total: number;
}

// ============================================================================
// Coverage Heatmap Types (FASE 1 - UI Improvements)
// ============================================================================

export interface TimeframeCoverageCell {
  status: 'complete' | 'partial' | 'missing';
  candles: number;
  expected: number | null;
}

export interface CoverageDateRow {
  date: string;
  timeframes: Record<string, TimeframeCoverageCell>;
}

export interface CoverageHeatMapResponse {
  symbol: string | null;
  date_range: {
    start: string;
    end: string;
  };
  coverage_matrix: CoverageDateRow[];
  summary: {
    complete: number;
    partial: number;
    missing: number;
  };
}

// ============================================================================
// Symbols List Types
// ============================================================================

export interface SymbolsList {
  symbols: string[];
  total: number;
}

// ============================================================================
// Integrity Check Types
// ============================================================================

export interface IntegrityTimeframeRow {
  timeframe: string;
  expected: number;
  actual: number;
  diff: number;
  status: 'ok' | 'mismatch' | 'warning';
}

export interface IntegrityRelationRow {
  relation: string;
  expected_ratio: number;
  actual_ratio: number;
  status: 'ok' | 'mismatch';
}

export interface IntegrityCheckResponse {
  symbol: string | null;
  start_date: string;
  end_date: string;
  total_trading_minutes: number;
  timeframe_checks: IntegrityTimeframeRow[];
  relation_checks: IntegrityRelationRow[];
  overall_status: 'ok' | 'warnings' | 'errors';
  summary: {
    ok: number;
    mismatch: number;
    warning: number;
  };
}

// Status colors for integrity checks
export const INTEGRITY_STATUS_COLORS = {
  ok: 'text-green-600 dark:text-green-400',
  warning: 'text-yellow-600 dark:text-yellow-400',
  mismatch: 'text-red-600 dark:text-red-400',
  errors: 'text-red-600 dark:text-red-400',
  warnings: 'text-yellow-600 dark:text-yellow-400',
} as const;

export const INTEGRITY_STATUS_BG_COLORS = {
  ok: 'bg-green-500/10 dark:bg-green-500/20',
  warning: 'bg-yellow-500/10 dark:bg-yellow-500/20',
  mismatch: 'bg-red-500/10 dark:bg-red-500/20',
  errors: 'bg-red-500/10 dark:bg-red-500/20',
  warnings: 'bg-yellow-500/10 dark:bg-yellow-500/20',
} as const;
