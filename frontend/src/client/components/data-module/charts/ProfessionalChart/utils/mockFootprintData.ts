import { FootprintCandle } from '../types';
import { roundToTickSize, NQ_TICK_SIZE, NQ_POINT_SIZE } from './priceUtils';

/**
 * Generate realistic mock footprint data for testing
 * This simulates what would come from the database's oflow_detail and oflow_unit JSONB fields
 */
export function generateMockFootprintCandle(
  time: number,
  open: number,
  high: number,
  low: number,
  close: number
): FootprintCandle {
  const oflowDetail: Record<string, { asks: number; bids: number }> = {};
  const oflowUnit: Record<string, { asks: number; bids: number }> = {};

  // Generate detail data (0.25 tick granularity)
  let maxVolume = 0;
  let maxVolumePrice = open;

  for (let price = low; price <= high; price += NQ_TICK_SIZE) {
    const roundedPrice = roundToTickSize(price, NQ_TICK_SIZE);

    // Generate realistic volume distribution (more volume near OHLC prices)
    const isImportantLevel =
      Math.abs(price - open) < 1 ||
      Math.abs(price - high) < 1 ||
      Math.abs(price - low) < 1 ||
      Math.abs(price - close) < 1;

    const baseVolume = isImportantLevel
      ? Math.floor(Math.random() * 500) + 200
      : Math.floor(Math.random() * 200) + 50;

    // Determine if bullish or bearish bias at this level
    const isBullishLevel = price < close;
    const bidBias = isBullishLevel ? 0.65 : 0.35;

    const totalVolume = baseVolume;
    const bidVolume = Math.floor(totalVolume * bidBias);
    const askVolume = totalVolume - bidVolume;

    oflowDetail[roundedPrice.toFixed(2)] = {
      asks: askVolume,
      bids: bidVolume,
    };

    // Track POC (highest volume level)
    if (totalVolume > maxVolume) {
      maxVolume = totalVolume;
      maxVolumePrice = roundedPrice;
    }
  }

  // Generate unit data (1.0 point granularity) by aggregating detail data
  for (let price = Math.floor(low); price <= Math.ceil(high); price += NQ_POINT_SIZE) {
    const roundedPrice = roundToTickSize(price, NQ_POINT_SIZE);

    let totalAsks = 0;
    let totalBids = 0;

    // Aggregate 4 ticks (0.25 * 4 = 1.0 point)
    for (let i = 0; i < 4; i++) {
      const tickPrice = (roundedPrice + i * NQ_TICK_SIZE).toFixed(2);
      const tickData = oflowDetail[tickPrice];

      if (tickData) {
        totalAsks += tickData.asks;
        totalBids += tickData.bids;
      }
    }

    if (totalAsks > 0 || totalBids > 0) {
      oflowUnit[roundedPrice.toFixed(2)] = {
        asks: totalAsks,
        bids: totalBids,
      };
    }
  }

  // Calculate total volume and delta
  let totalVolume = 0;
  let totalDelta = 0;

  Object.values(oflowDetail).forEach(({ asks, bids }) => {
    totalVolume += asks + bids;
    totalDelta += bids - asks;
  });

  // Simulate absorption metrics (simplified)
  const wickRange = high - low;
  const asellersUwick = Math.floor(Math.random() * wickRange * 100);
  const abuyersLwick = Math.floor(Math.random() * wickRange * 100);

  return {
    time_interval: new Date(time * 1000).toISOString(),
    symbol: 'NQ',
    open,
    high,
    low,
    close,
    volume: totalVolume,
    delta: totalDelta,
    oflow_detail: oflowDetail,
    oflow_unit: oflowUnit,
    real_poc: maxVolumePrice,
    real_poc_volume: maxVolume,
    asellers_uwick: asellersUwick,
    abuyers_lwick: abuyersLwick,
  };
}

/**
 * Generate mock footprint data for date range
 */
export function generateMockFootprintData(
  startDate: Date,
  endDate: Date,
  intervalMs: number = 5 * 60 * 1000 // 5 minutes default
): FootprintCandle[] {
  const data: FootprintCandle[] = [];
  let basePrice = 20600; // Realistic NQ price around 20600

  let currentTime = startDate.getTime();
  const endTime = endDate.getTime();

  while (currentTime <= endTime) {
    // Realistic range: 5-30 points per candle (20-120 ticks), mean 15 points (60 ticks)
    const rangeInPoints = 5 + Math.random() * 25;
    const rangeInPrice = rangeInPoints;

    const drift = (Math.random() - 0.5) * 5;
    const open = basePrice + drift;
    const closeDirection = Math.random() > 0.5 ? 1 : -1;
    const close = open + closeDirection * (Math.random() * rangeInPrice);

    const high = Math.max(open, close) + Math.random() * (rangeInPrice * 0.3);
    const low = Math.min(open, close) - Math.random() * (rangeInPrice * 0.3);

    const candle = generateMockFootprintCandle(
      Math.floor(currentTime / 1000),
      open,
      high,
      low,
      close
    );

    data.push(candle);

    basePrice = close;
    currentTime += intervalMs;
  }

  return data;
}

/**
 * Generate mock footprint data from existing candles
 * This ensures footprint aligns perfectly with candle OHLC values
 */
export function generateMockFootprintFromCandles(
  candles: Array<{
    time: any;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>
): FootprintCandle[] {
  return candles.map(candle => {
    // Use the EXACT OHLC values from the candle
    const footprintCandle = generateMockFootprintCandle(
      typeof candle.time === 'number' ? candle.time : Math.floor(new Date(candle.time).getTime() / 1000),
      candle.open,
      candle.high,
      candle.low,
      candle.close
    );

    return footprintCandle;
  });
}
