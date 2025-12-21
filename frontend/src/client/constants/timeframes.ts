/**
 * Timeframe Constants
 *
 * Defines the 9 supported timeframes for market state snapshots
 */

export const TIMEFRAMES = [
  '30s',
  '1min',
  '5min',
  '15min',
  '30min',
  '1hr',
  '4hr',
  'daily',
  'weekly'
] as const;

export type Timeframe = typeof TIMEFRAMES[number];

export const TIMEFRAME_LABELS: Record<Timeframe, string> = {
  '30s': '30 Seconds',
  '1min': '1 Minute',
  '5min': '5 Minutes',
  '15min': '15 Minutes',
  '30min': '30 Minutes',
  '1hr': '1 Hour',
  '4hr': '4 Hours',
  'daily': 'Daily',
  'weekly': 'Weekly'
};

export const TIMEFRAME_SHORT_LABELS: Record<Timeframe, string> = {
  '30s': '30s',
  '1min': '1m',
  '5min': '5m',
  '15min': '15m',
  '30min': '30m',
  '1hr': '1h',
  '4hr': '4h',
  'daily': '1D',
  'weekly': '1W'
};
