/**
 * Pattern Detection Types
 *
 * TypeScript interfaces for FVG, Liquidity Pool, and Order Block detection
 */

// ============================================================================
// FVG Types
// ============================================================================

export interface FVGDetectionRequest {
  symbol: string;
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  timeframe?: string; // default: "5min"
}

export interface FVGResponse {
  fvg_id: number;
  symbol: string;
  timeframe: string;
  formation_time: string;
  fvg_type: "BULLISH" | "BEARISH";
  fvg_start: number;
  fvg_end: number;
  gap_size: number;
  midpoint: number;
  vela1_high: number;
  vela1_low: number;
  vela3_high: number;
  vela3_low: number;
  significance: "MICRO" | "SMALL" | "MEDIUM" | "LARGE" | "EXTREME";

  // ICT-specific fields
  premium_level?: number;
  discount_level?: number;
  consequent_encroachment?: number;
  displacement_score?: number;
  has_break_of_structure?: boolean;

  status: "UNMITIGATED" | "REDELIVERED" | "REBALANCED";
  last_checked_time?: string;
  created_at: string;
}

export interface FVGGenerationResponse {
  total: number;
  auto_parameters: {
    min_gap_size: number;
    timeframe: string;
    symbol: string;
  };
  state_update_stats?: {
    total_checked: number;
    redelivered: number;
    rebalanced: number;
  };
  fvgs: FVGResponse[];
  text_report: string; // Markdown formatted report
}

export interface FVGListResponse {
  total: number;
  fvgs: FVGResponse[];
}

// ============================================================================
// Liquidity Pool Types
// ============================================================================

export interface LiquidityPoolDetectionRequest {
  symbol: string;
  date: string;      // YYYY-MM-DD (single date, not range)
  timeframe?: string; // default: "5min"
  pool_types?: string[]; // Optional filter: ["EQH", "EQL", "SESSION"]
}

export interface LiquidityPoolResponse {
  lp_id: number;
  symbol: string;
  timeframe: string;
  formation_time: string;
  pool_type: "EQH" | "EQL" | "ASH" | "ASL" | "LSH" | "LSL" | "NYH" | "NYL";
  level: number;
  zone_low?: number; // For EQH/EQL pools (zones), null for session levels
  zone_high?: number; // For EQH/EQL pools (zones), null for session levels
  tolerance: number;
  touch_times: string[];
  num_touches: number;
  total_volume: number | null;
  strength: "STRONG" | "NORMAL" | "WEAK";
  status: "UNMITIGATED" | "RESPECTED" | "SWEPT" | "MITIGATED";
  created_at: string;

  // Rectangle representation fields (computed from touch_times)
  start_time?: string; // Rectangle start (first touch)
  end_time?: string;   // Rectangle end (last touch)
  liquidity_type?: string; // "Buy-Side Liquidity" or "Sell-Side Liquidity"
  zone_size?: number;  // Rectangle height in points
}

export interface LiquidityPoolGenerationResponse {
  total: number;
  breakdown: Record<string, number>;
  auto_parameters: {
    tolerance: number;
    timeframe: string;
    symbol: string;
    min_touches_eqh_eql: number;
    min_touches_triple: number;
    swing_lookback: number;
  };
  pools: LiquidityPoolResponse[];
  text_report: string; // Markdown formatted report
}

export interface LiquidityPoolListResponse {
  total: number;
  pools: LiquidityPoolResponse[];
}

// ============================================================================
// Order Block Types
// ============================================================================

export interface OrderBlockDetectionRequest {
  symbol: string;
  start_date: string; // YYYY-MM-DD
  end_date: string;   // YYYY-MM-DD
  timeframe?: string; // default: "5min"
}

export interface OrderBlockResponse {
  ob_id: number;
  symbol: string;
  timeframe: string;
  formation_time: string;
  ob_type: "BULLISH OB" | "BEARISH OB" | "STRONG BULLISH OB" | "STRONG BEARISH OB";
  ob_high: number;
  ob_low: number;
  ob_open: number;
  ob_close: number;
  ob_volume: number;
  impulse_move: number;
  impulse_direction: "UP" | "DOWN";
  candle_direction: "BULLISH" | "BEARISH" | "DOJI";
  quality: "HIGH" | "MEDIUM" | "LOW";
  status: "ACTIVE" | "TESTED" | "BROKEN";
  created_at: string;
}

export interface OrderBlockGenerationResponse {
  total: number;
  breakdown: Record<string, number>;
  auto_parameters: {
    min_impulse: number;
    strong_threshold: number;
    lookforward_candles: number;
    timeframe: string;
    symbol: string;
  };
  order_blocks: OrderBlockResponse[];
  text_report: string; // Markdown formatted report
}

export interface OrderBlockListResponse {
  total: number;
  order_blocks: OrderBlockResponse[];
}

// ============================================================================
// Pattern Interaction Types
// ============================================================================

export interface PatternInteractionResponse {
  interaction_id: number;
  pattern_type: "FVG" | "LP" | "OB";
  pattern_id: number;
  interaction_time: string;
  interaction_type:
    | "R0_CLEAN_BOUNCE"
    | "R1_SHALLOW_TOUCH"
    | "R2_LIGHT_REJECTION"
    | "R3_MEDIUM_REJECTION"
    | "R4_DEEP_REJECTION"
    | "P1_SHALLOW_PENETRATION"
    | "P2_DEEP_PENETRATION"
    | "P3_FULL_PENETRATION"
    | "P4_FALSE_BREAKOUT"
    | "P5_BREAK_AND_RETEST";
  penetration_pts: number;
  penetration_pct: number;
  confidence: number;
  candle_high: number;
  candle_low: number;
  candle_close: number;
  created_at: string;
}

export interface PatternInteractionsResponse {
  total: number;
  breakdown: Record<string, number>;
  interactions: PatternInteractionResponse[];
  text_report: string; // Markdown formatted report
}

// ============================================================================
// Market State Types
// ============================================================================

export interface MarketStateGenerateRequest {
  symbol: string;
  start_time: string; // ISO 8601: "2025-11-24T09:00:00"
  end_time: string;   // ISO 8601: "2025-11-24T16:00:00"
  interval_minutes?: number; // 1-60, default: 5
}

export interface TimeframeSummary {
  active_fvgs_count: number;
  active_lps_count: number;
  active_obs_count: number;
  bullish_count: number;
  bearish_count: number;
}

export interface TimeframeData {
  summary: TimeframeSummary;
  active_fvgs: FVGResponse[];
  active_session_levels: LiquidityPoolResponse[];
  active_obs: OrderBlockResponse[];
}

export interface MarketStateSummary {
  total_patterns_all_timeframes: number;
  by_timeframe: Record<string, number>; // {"30s": 3, "1min": 8, ...}
}

export interface MarketStateDetailResponse {
  snapshot_time: string;
  snapshot_time_est: string; // Formatted: "2025-11-24 04:30:00 EST"
  symbol: string;
  summary: MarketStateSummary;
  timeframes: Record<string, TimeframeData>; // {"30s": {...}, "1min": {...}, ...}
}

export interface MarketStateSnapshotInfo {
  snapshot_time: string;
  snapshot_time_est: string;
  total_patterns: number;
  by_timeframe: Record<string, number>;
}

export interface MarketStateGenerateResponse {
  job_id: string;
  total_snapshots: number;
  symbol: string;
  start_time: string;
  end_time: string;
  snapshots: MarketStateSnapshotInfo[];
}

export interface MarketStateProgressResponse {
  job_id: string;
  symbol: string;
  total_snapshots: number;
  completed_snapshots: number;
  percentage: number;
  status: "running" | "completed" | "error";
  elapsed_seconds: number;
  estimated_seconds_remaining: number;
  error_message?: string;
}

export interface MarketStateListResponse {
  total: number;
  symbol: string;
  snapshots: Array<{
    snapshot_id: number;
    snapshot_time: string;
    snapshot_time_est: string;
    total_patterns: number;
    by_timeframe: Record<string, number>;
    created_at: string;
  }>;
}
