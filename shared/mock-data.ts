/**
 * MOCK DATA FOR DEVELOPMENT
 * 
 * This file contains all mock data used in the Data Module.
 * Replace the mock functions with actual API calls when backend is ready.
 * 
 * VARIABLES TO REPLACE WITH API ENDPOINTS:
 * - OHLCV_DATA_ENDPOINT: GET /api/chart/candles?symbol=NQ&timeframe=1h&start=...&end=...
 * - FOOTPRINT_DATA_ENDPOINT: GET /api/chart/footprint?symbol=NQ&timeframe=1h&start=...&end=...
 * - VOLUME_PROFILE_ENDPOINT: GET /api/chart/volume-profile?symbol=NQ&timeframe=1h&start=...&end=...
 * - DELTA_PROFILE_ENDPOINT: GET /api/chart/delta-profile?symbol=NQ&timeframe=1h&start=...&end=...
 * - ETL_STATUS_ENDPOINT: GET /api/etl/status
 * - DATA_SOURCES_ENDPOINT: GET /api/etl/sources
 * - JOBS_ENDPOINT: GET /api/etl/jobs
 */

// ==================== OHLCV DATA ====================
export interface OHLCVCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * REPLACE: generateMockOHLCVData()
 * WITH: GET /api/chart/candles?symbol={symbol}&timeframe={timeframe}&start={startDate}&end={endDate}
 */
export function generateMockOHLCVData(
  count: number = 100,
  basePrice: number = 18500
): OHLCVCandle[] {
  const data: OHLCVCandle[] = [];
  const now = Date.now();
  const interval = 60 * 60 * 1000; // 1 hour

  for (let i = count; i > 0; i--) {
    const timestamp = now - i * interval;
    const volatility = Math.random() * 200 - 100;
    const baseVol = 1000000 + Math.random() * 2000000;

    const open = basePrice + volatility;
    const close = open + (Math.random() * 400 - 200);
    const high = Math.max(open, close) + Math.random() * 150;
    const low = Math.min(open, close) - Math.random() * 150;

    data.push({
      timestamp,
      open,
      high,
      low,
      close,
      volume: Math.round(baseVol),
    });

    basePrice = close;
  }

  return data;
}

// ==================== FOOTPRINT DATA ====================
export interface FootprintLevel {
  price: number;
  buyVolume: number;
  sellVolume: number;
  totalVolume: number;
  delta: number;
}

export interface FootprintCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  levels: FootprintLevel[];
}

/**
 * REPLACE: generateMockFootprintData()
 * WITH: GET /api/chart/footprint?symbol={symbol}&timeframe={timeframe}&start={startDate}&end={endDate}
 */
export function generateMockFootprintData(count: number = 50): FootprintCandle[] {
  const data: FootprintCandle[] = [];
  const now = Date.now();
  const interval = 60 * 60 * 1000;

  for (let i = count; i > 0; i--) {
    const timestamp = now - i * interval;
    const basePrice = 18500 + (Math.random() * 1000 - 500);
    const open = basePrice;
    const close = basePrice + (Math.random() * 400 - 200);
    const high = Math.max(open, close) + 100;
    const low = Math.min(open, close) - 100;

    const levels: FootprintLevel[] = [];
    const levelCount = Math.floor(Math.random() * 10) + 20;

    for (let p = Math.floor(low); p <= Math.ceil(high); p += Math.ceil((high - low) / levelCount)) {
      const buyVol = Math.floor(Math.random() * 50000);
      const sellVol = Math.floor(Math.random() * 50000);
      levels.push({
        price: p,
        buyVolume: buyVol,
        sellVolume: sellVol,
        totalVolume: buyVol + sellVol,
        delta: buyVol - sellVol,
      });
    }

    data.push({ timestamp, open, high, low, close, levels });
  }

  return data;
}

// ==================== VOLUME PROFILE ====================
export interface VolumeProfileNode {
  price: number;
  volume: number;
  percentage: number;
}

/**
 * REPLACE: generateMockVolumeProfile()
 * WITH: GET /api/chart/volume-profile?symbol={symbol}&timeframe={timeframe}&start={startDate}&end={endDate}
 */
export function generateMockVolumeProfile(
  minPrice: number = 18300,
  maxPrice: number = 18700
): VolumeProfileNode[] {
  const data: VolumeProfileNode[] = [];
  const steps = 50;
  const priceStep = (maxPrice - minPrice) / steps;
  const totalVolume = 50000000;

  for (let i = 0; i < steps; i++) {
    const price = minPrice + i * priceStep;
    const volume = Math.floor(Math.random() * 2000000);
    data.push({
      price,
      volume,
      percentage: (volume / totalVolume) * 100,
    });
  }

  return data.sort((a, b) => b.volume - a.volume).slice(0, 20);
}

// ==================== DELTA PROFILE ====================
export interface DeltaProfileNode {
  timestamp: number;
  cumulativeDelta: number;
  buyVolume: number;
  sellVolume: number;
}

/**
 * REPLACE: generateMockDeltaProfile()
 * WITH: GET /api/chart/delta-profile?symbol={symbol}&timeframe={timeframe}&start={startDate}&end={endDate}
 */
export function generateMockDeltaProfile(count: number = 100): DeltaProfileNode[] {
  const data: DeltaProfileNode[] = [];
  const now = Date.now();
  const interval = 1000 * 60; // 1 minute
  let cumulativeDelta = 0;

  for (let i = count; i > 0; i--) {
    const timestamp = now - i * interval;
    const buyVol = Math.floor(Math.random() * 100000);
    const sellVol = Math.floor(Math.random() * 100000);
    const delta = buyVol - sellVol;
    cumulativeDelta += delta;

    data.push({
      timestamp,
      cumulativeDelta,
      buyVolume: buyVol,
      sellVolume: sellVol,
    });
  }

  return data;
}

// ==================== ETL DATA ====================
export interface DataSource {
  id: string;
  name: string;
  provider: "databento" | "other";
  status: "connected" | "disconnected" | "error";
  lastSync: Date;
  instruments: string[];
}

/**
 * REPLACE: getMockDataSources()
 * WITH: GET /api/etl/sources
 */
export function getMockDataSources(): DataSource[] {
  return [
    {
      id: "databento-nq",
      name: "Databento - NQ Futures",
      provider: "databento",
      status: "connected",
      lastSync: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
      instruments: ["NQ"],
    },
    {
      id: "databento-news",
      name: "Databento - News Feed",
      provider: "databento",
      status: "connected",
      lastSync: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
      instruments: ["NQ"],
    },
  ];
}

export interface ETLJob {
  id: string;
  name: string;
  status: "running" | "completed" | "failed" | "scheduled";
  progress: number;
  startTime: Date;
  endTime?: Date;
  dataSource: string;
  recordsProcessed: number;
}

/**
 * REPLACE: getMockETLJobs()
 * WITH: GET /api/etl/jobs
 */
export function getMockETLJobs(): ETLJob[] {
  return [
    {
      id: "job-1",
      name: "NQ Price Data Sync",
      status: "completed",
      progress: 100,
      startTime: new Date(Date.now() - 30 * 60 * 1000),
      endTime: new Date(Date.now() - 25 * 60 * 1000),
      dataSource: "databento-nq",
      recordsProcessed: 50000,
    },
    {
      id: "job-2",
      name: "News Feed Update",
      status: "running",
      progress: 65,
      startTime: new Date(Date.now() - 5 * 60 * 1000),
      dataSource: "databento-news",
      recordsProcessed: 325,
    },
    {
      id: "job-3",
      name: "Transform to Timeframes",
      status: "scheduled",
      progress: 0,
      startTime: new Date(Date.now() + 5 * 60 * 1000),
      dataSource: "databento-nq",
      recordsProcessed: 0,
    },
  ];
}

export interface ETLStatus {
  isRunning: boolean;
  totalRecords: number;
  lastUpdate: Date;
  health: "healthy" | "warning" | "error";
}

/**
 * REPLACE: getMockETLStatus()
 * WITH: GET /api/etl/status
 */
export function getMockETLStatus(): ETLStatus {
  return {
    isRunning: true,
    totalRecords: 2500000,
    lastUpdate: new Date(Date.now() - 2 * 60 * 1000),
    health: "healthy",
  };
}

// ==================== INDICATOR DATA ====================
export interface IndicatorValue {
  timestamp: number;
  value: number;
}

/**
 * REPLACE: generateMockSMAData()
 * WITH: GET /api/indicators/sma?symbol={symbol}&period={period}&timeframe={timeframe}
 */
export function generateMockSMAData(
  ohlcvData: OHLCVCandle[],
  period: number = 20
): IndicatorValue[] {
  const result: IndicatorValue[] = [];

  for (let i = period - 1; i < ohlcvData.length; i++) {
    const sum = ohlcvData.slice(i - period + 1, i + 1).reduce((acc, c) => acc + c.close, 0);
    result.push({
      timestamp: ohlcvData[i].timestamp,
      value: sum / period,
    });
  }

  return result;
}

/**
 * REPLACE: generateMockRSIData()
 * WITH: GET /api/indicators/rsi?symbol={symbol}&period={period}&timeframe={timeframe}
 */
export function generateMockRSIData(ohlcvData: OHLCVCandle[], period: number = 14): IndicatorValue[] {
  const result: IndicatorValue[] = [];
  const closes = ohlcvData.map((c) => c.close);

  for (let i = period; i < closes.length; i++) {
    let gains = 0;
    let losses = 0;

    for (let j = i - period + 1; j <= i; j++) {
      const change = closes[j] - closes[j - 1];
      if (change > 0) gains += change;
      else losses -= change;
    }

    const avgGain = gains / period;
    const avgLoss = losses / period;
    const rs = avgGain / (avgLoss || 1);
    const rsi = 100 - 100 / (1 + rs);

    result.push({
      timestamp: ohlcvData[i].timestamp,
      value: rsi,
    });
  }

  return result;
}
