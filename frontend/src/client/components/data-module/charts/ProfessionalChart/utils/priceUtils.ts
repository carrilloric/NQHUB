import { PriceRange } from '../types';

/**
 * Price utility functions for footprint and volume profile calculations
 */

// NQ Futures tick size is 0.25
export const NQ_TICK_SIZE = 0.25;
export const NQ_POINT_SIZE = 1.0;

export function roundToTickSize(price: number, tickSize: number = NQ_TICK_SIZE): number {
  return Math.round(price / tickSize) * tickSize;
}

export function generatePriceLevels(
  low: number,
  high: number,
  tickSize: number = NQ_TICK_SIZE
): number[] {
  const levels: number[] = [];
  const start = roundToTickSize(low, tickSize);
  const end = roundToTickSize(high, tickSize);

  for (let price = start; price <= end; price += tickSize) {
    levels.push(roundToTickSize(price, tickSize));
  }

  return levels;
}

export function calculatePriceRange(candles: Array<{ high: number; low: number }>): PriceRange {
  if (candles.length === 0) {
    return { min: 0, max: 0, tickSize: NQ_TICK_SIZE };
  }

  const min = Math.min(...candles.map(c => c.low));
  const max = Math.max(...candles.map(c => c.high));

  return {
    min: roundToTickSize(min),
    max: roundToTickSize(max),
    tickSize: NQ_TICK_SIZE,
  };
}

export function getPriceLevelKey(price: number, tickSize: number = NQ_TICK_SIZE): string {
  const rounded = roundToTickSize(price, tickSize);
  return rounded.toFixed(2);
}

export function formatPrice(price: number, decimals: number = 2): string {
  return price.toFixed(decimals);
}

export function calculateImbalance(bidVolume: number, askVolume: number): number {
  const total = bidVolume + askVolume;
  if (total === 0) return 0;

  const larger = Math.max(bidVolume, askVolume);
  const smaller = Math.min(bidVolume, askVolume);

  if (smaller === 0) return Infinity;

  return larger / smaller;
}

export function isDominant(
  bidVolume: number,
  askVolume: number,
  threshold: number = 1.5
): 'bid' | 'ask' | 'neutral' {
  const imbalance = calculateImbalance(bidVolume, askVolume);

  if (imbalance < threshold) return 'neutral';

  return bidVolume > askVolume ? 'bid' : 'ask';
}

export function calculateDelta(bidVolume: number, askVolume: number): number {
  return bidVolume - askVolume;
}

export function isWithinCandle(
  price: number,
  open: number,
  high: number,
  low: number,
  close: number
): 'upper_wick' | 'body' | 'lower_wick' | 'outside' {
  if (price > high || price < low) return 'outside';

  const bodyTop = Math.max(open, close);
  const bodyBottom = Math.min(open, close);

  if (price > bodyTop && price <= high) return 'upper_wick';
  if (price < bodyBottom && price >= low) return 'lower_wick';
  return 'body';
}

export function calculatePercentageOfRange(
  value: number,
  min: number,
  max: number
): number {
  if (max === min) return 0;
  return ((value - min) / (max - min)) * 100;
}
