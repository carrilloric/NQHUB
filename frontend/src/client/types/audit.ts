/**
 * Audit Module Types
 *
 * Types for the audit module used to validate detected patterns against ATAS.
 */

/**
 * Request to generate Order Blocks audit report
 */
export interface AuditOrderBlocksRequest {
  symbol: string;
  timeframe: string;
  snapshot_time: string; // ISO 8601 datetime string
}

/**
 * Single Order Block for audit validation
 */
export interface OrderBlockAuditItem {
  ob_id: number;
  ob_type: string; // BULLISH OB, BEARISH OB, STRONG BULLISH OB, STRONG BEARISH OB
  formation_time_est: string; // Formatted: "Nov 6, 2025 05:20:00 EST"
  formation_time_utc: string; // For reference
  zone_low: number;
  zone_high: number;
  body_midpoint: number;
  range_midpoint: number;
  status: string; // ACTIVE, TESTED, BROKEN
  quality: string; // HIGH, MEDIUM, LOW
  impulse_move: number;
  impulse_direction: string; // UP, DOWN
  candle_direction: string; // BULLISH, BEARISH
  ob_open: number;
  ob_close: number;
  ob_volume: number;
}

/**
 * Response with Order Blocks audit report
 */
export interface AuditOrderBlocksResponse {
  report_markdown: string; // Markdown formatted report
  total_obs: number; // Total ACTIVE OBs at snapshot
  snapshot_time_est: string; // Formatted: "Nov 24, 2025 09:30:00 EST"
  snapshot_time_utc: string;
  symbol: string;
  timeframe: string;
  order_blocks: OrderBlockAuditItem[]; // Full data for programmatic access
}
