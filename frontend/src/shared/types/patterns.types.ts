/**
 * Pattern Detection Types
 * Based on CONTRACT-002 specification
 */

// Enums
export type Timeframe = '1min' | '5min' | '15min' | '30min' | '1hour' | '4hour' | '1day';

export type FVGStatus = 'UNMITIGATED' | 'REDELIVERED' | 'REBALANCED';
export type FVGSignificance = 'MICRO' | 'SMALL' | 'MEDIUM' | 'LARGE' | 'EXTREME';
export type FVGDirection = 'BULLISH' | 'BEARISH';

export type OrderBlockType = 'BULLISH OB' | 'BEARISH OB' | 'STRONG BULLISH OB' | 'STRONG BEARISH OB';
export type OrderBlockQuality = 'HIGH' | 'MEDIUM' | 'LOW';
export type OrderBlockStatus = 'ACTIVE' | 'TESTED' | 'BROKEN';
export type ImpulseDirection = 'UP' | 'DOWN';

export type LiquidityPoolType = 'EQH' | 'EQL' | 'NYH' | 'NYL' | 'ASH' | 'ASL' | 'LSH' | 'LSL' | 'SWING_HIGH' | 'SWING_LOW';
export type LiquidityPoolStrength = 'STRONG' | 'NORMAL' | 'WEAK';
export type LiquidityPoolStatus = 'UNMITIGATED' | 'RESPECTED' | 'SWEPT' | 'MITIGATED';

export type InteractionType = 'R0' | 'R1' | 'R2' | 'R3' | 'R4' | 'P1' | 'P2' | 'P3' | 'P4' | 'P5';
export type PatternType = 'FVG' | 'OB' | 'LP';

// Fair Value Gap Pattern
export interface FVGPattern {
  id: number;
  symbol: string;
  timeframe: Timeframe;
  formation_time: string; // ISO date-time
  gap_high: number;
  gap_low: number;
  gap_size_pts: number;
  gap_size_pct: number;
  significance: FVGSignificance;
  status: FVGStatus;
  direction?: FVGDirection;
  premium_level?: number;
  discount_level?: number;
  consequent_encroachment?: number; // 50% level (ICT concept)
  displacement_score?: number;
  has_break_of_structure?: boolean;
  mitigation_time?: string | null; // ISO date-time
  mitigation_candle_id?: number | null;
}

// Order Block Pattern
export interface OrderBlockPattern {
  id: number;
  symbol: string;
  timeframe: Timeframe;
  formation_time: string; // ISO date-time
  ob_high: number;
  ob_low: number;
  ob_type: OrderBlockType;
  quality: OrderBlockQuality;
  status: OrderBlockStatus;
  ob_body_midpoint?: number; // 50% of candle body
  ob_range_midpoint?: number; // 50% of candle range
  impulse_move?: number;
  impulse_direction?: ImpulseDirection;
  volume?: number;
  test_time?: string | null; // ISO date-time
  break_time?: string | null; // ISO date-time
}

// Liquidity Pool Pattern
export interface LiquidityPoolPattern {
  id: number;
  symbol: string;
  timeframe: Timeframe;
  formation_time: string; // ISO date-time
  zone_high: number;
  zone_low: number;
  pool_type: LiquidityPoolType;
  strength: LiquidityPoolStrength;
  status: LiquidityPoolStatus;
  modal_level?: number; // Price level with most touches
  touches?: number; // Number of times price touched the zone
  sweep_time?: string | null; // ISO date-time
  mitigation_time?: string | null; // ISO date-time
}

// Market State Snapshot
export interface MarketStateSnapshot {
  timestamp: string; // ISO date-time (UTC)
  symbol: string;
  timeframe: Timeframe;
  current_price?: number;
  active_patterns: {
    fvgs: Array<{
      id: number;
      gap_high: number;
      gap_low: number;
      significance: FVGSignificance;
    }>;
    order_blocks: Array<{
      id: number;
      ob_high: number;
      ob_low: number;
      ob_type: OrderBlockType;
    }>;
    liquidity_pools: Array<{
      id: number;
      zone_high: number;
      zone_low: number;
      pool_type: LiquidityPoolType;
    }>;
  };
  summary?: {
    total_active_fvgs: number;
    total_active_obs: number;
    total_active_lps: number;
    nearest_resistance?: number | null;
    nearest_support?: number | null;
  };
}

// Pattern Interaction
export interface PatternInteraction {
  id: number;
  pattern_type: PatternType;
  pattern_id: number;
  interaction_time: string; // ISO date-time
  interaction_type: InteractionType;
  penetration_pts: number;
  penetration_pct: number;
  candle_high?: number;
  candle_low?: number;
  candle_close?: number;
  volume?: number;
  confidence?: number; // 0-1
}

// API Response types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface PaginatedInteractionResponse extends PaginatedResponse<PatternInteraction> {
  summary?: {
    by_type: Record<InteractionType, number>;
  };
}

// Filter types for API calls
export interface PatternFilters {
  symbol: string;
  timeframe?: Timeframe;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface FVGFilters extends PatternFilters {
  status?: FVGStatus;
  significance?: FVGSignificance;
  sort_by?: 'formation_time' | 'gap_size_pts' | 'significance';
}

export interface OrderBlockFilters extends PatternFilters {
  status?: OrderBlockStatus;
  ob_type?: OrderBlockType;
  quality?: OrderBlockQuality;
  sort_by?: 'formation_time' | 'impulse_move' | 'quality';
}

export interface LiquidityPoolFilters extends PatternFilters {
  status?: LiquidityPoolStatus;
  pool_type?: LiquidityPoolType;
  strength?: LiquidityPoolStrength;
  sort_by?: 'formation_time' | 'touches' | 'strength';
}

export interface InteractionFilters {
  pattern_type?: PatternType;
  pattern_id?: number;
  interaction_type?: InteractionType;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  page?: number;
  page_size?: number;
}

// Error response
export interface PatternErrorResponse {
  detail: string;
  code: 'VALIDATION_ERROR' | 'NOT_FOUND' | 'INTERNAL_ERROR' | 'UNAUTHORIZED' | 'FORBIDDEN';
}