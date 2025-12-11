import { FootprintCandle, FootprintLevel, OrderFlowLevel } from '../types';
import { roundToTickSize, NQ_TICK_SIZE } from '../utils/priceUtils';
import { isDominant } from '../utils/priceUtils';

/**
 * Parse JSONB order flow data from database into FootprintLevel array
 *
 * Example input format:
 * {
 *   "19875.00": { "asks": 125, "bids": 98 },
 *   "19875.25": { "asks": 87, "bids": 142 }
 * }
 */
export function parseOrderFlowData(
  oflowData: Record<string, { asks: number; bids: number }>,
  poc?: number,
  tickSize: number = NQ_TICK_SIZE
): FootprintLevel[] {
  if (!oflowData || typeof oflowData !== 'object') {
    return [];
  }

  const levels: FootprintLevel[] = [];

  // Parse each price level
  Object.entries(oflowData).forEach(([priceStr, volumes]) => {
    const price = parseFloat(priceStr);

    if (isNaN(price) || !volumes) {
      return;
    }

    const askVolume = volumes.asks || 0;
    const bidVolume = volumes.bids || 0;
    const totalVolume = askVolume + bidVolume;

    // Calculate delta (bid - ask, positive = buying pressure)
    const delta = bidVolume - askVolume;

    // Determine dominance
    const dominance = isDominant(bidVolume, askVolume, 1.5);

    // Check if this is the POC
    const isPOC = poc !== undefined && Math.abs(price - poc) < tickSize / 2;

    // Calculate imbalance ratio (for color intensity)
    const imbalanceRatio = totalVolume > 0
      ? Math.max(bidVolume, askVolume) / Math.min(bidVolume, askVolume)
      : 1;

    levels.push({
      price: roundToTickSize(price, tickSize),
      askVolume,
      bidVolume,
      totalVolume,
      delta,
      isDominant: dominance,
      isPOC,
      imbalanceRatio,
    });
  });

  // Sort by price descending (high to low for rendering)
  const sortedByPrice = levels.sort((a, b) => b.price - a.price);

  // Ensure at least one POC exists - if no POC was matched, mark the highest volume level
  const hasPOC = sortedByPrice.some(level => level.isPOC);
  if (!hasPOC && sortedByPrice.length > 0) {
    // Find the level with maximum total volume
    let maxVolumeLevel = sortedByPrice[0];
    let maxVolume = maxVolumeLevel.totalVolume;

    sortedByPrice.forEach(level => {
      if (level.totalVolume > maxVolume) {
        maxVolume = level.totalVolume;
        maxVolumeLevel = level;
      }
    });

    // Mark this level as POC
    maxVolumeLevel.isPOC = true;
  }

  // If we have too many levels (> 8), filter to show evenly spaced ones
  if (sortedByPrice.length > 8) {
    const maxLevels = 8;
    const step = Math.floor(sortedByPrice.length / maxLevels);
    const filteredLevels: FootprintLevel[] = [];

    // Always include the POC level
    const pocLevel = sortedByPrice.find(level => level.isPOC);

    for (let i = 0; i < sortedByPrice.length && filteredLevels.length < maxLevels; i += step) {
      filteredLevels.push(sortedByPrice[i]);
    }

    // If POC wasn't included in the filtered list, replace the closest level
    if (pocLevel && !filteredLevels.some(level => level.isPOC)) {
      // Find the closest level to POC
      let closestIndex = 0;
      let minDiff = Math.abs(filteredLevels[0].price - pocLevel.price);

      for (let i = 1; i < filteredLevels.length; i++) {
        const diff = Math.abs(filteredLevels[i].price - pocLevel.price);
        if (diff < minDiff) {
          minDiff = diff;
          closestIndex = i;
        }
      }

      // Replace the closest level with POC
      filteredLevels[closestIndex] = pocLevel;
    }

    return filteredLevels;
  }

  return sortedByPrice;
}

/**
 * Convert FootprintCandle from database into parsed FootprintLevel array
 * Uses oflow_detail (0.25 tick) for high zoom, oflow_unit (1.0 point) for lower zoom
 */
export function parseFootprintCandle(
  candle: FootprintCandle,
  useDetailedData: boolean = true
): {
  levels: FootprintLevel[];
  candleData: {
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    delta: number;
    poc: number;
    pocVolume: number;
  };
} {
  // Choose which JSONB field to use based on zoom level
  const oflowData = useDetailedData ? candle.oflow_detail : candle.oflow_unit;

  // Parse the order flow data
  const levels = parseOrderFlowData(oflowData, candle.real_poc);

  // Calculate total candle metrics
  const totalDelta = levels.reduce((sum, level) => sum + level.delta, 0);
  const totalVolume = levels.reduce((sum, level) => sum + level.totalVolume, 0);

  return {
    levels,
    candleData: {
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
      volume: candle.volume || totalVolume,
      delta: candle.delta || totalDelta,
      poc: candle.real_poc,
      pocVolume: candle.real_poc_volume,
    },
  };
}

/**
 * Get footprint data for multiple candles
 * Returns array of parsed candles with their footprint levels
 */
export function parseFootprintCandles(
  candles: FootprintCandle[],
  useDetailedData: boolean = true
): Array<{
  timeInterval: string;
  symbol: string;
  levels: FootprintLevel[];
  candleData: ReturnType<typeof parseFootprintCandle>['candleData'];
}> {
  return candles.map(candle => {
    const parsed = parseFootprintCandle(candle, useDetailedData);

    return {
      timeInterval: candle.time_interval,
      symbol: candle.symbol,
      levels: parsed.levels,
      candleData: parsed.candleData,
    };
  });
}

/**
 * Validate JSONB order flow data structure
 */
export function validateOrderFlowData(
  data: unknown
): data is Record<string, { asks: number; bids: number }> {
  if (!data || typeof data !== 'object') {
    return false;
  }

  const entries = Object.entries(data);

  if (entries.length === 0) {
    return false;
  }

  // Check that all entries have valid structure
  return entries.every(([priceStr, volumes]) => {
    // Check price is a valid number string
    const price = parseFloat(priceStr);
    if (isNaN(price)) {
      return false;
    }

    // Check volumes object structure
    if (!volumes || typeof volumes !== 'object') {
      return false;
    }

    const { asks, bids } = volumes as any;

    return (
      typeof asks === 'number' &&
      typeof bids === 'number' &&
      asks >= 0 &&
      bids >= 0
    );
  });
}
