import { Time } from 'lightweight-charts';

// ==================== OHLCV Types ====================

export interface OHLCVCandle {
  time_interval: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  is_spread: boolean;
  is_rollover_period: boolean;
}

// ==================== Order Flow Types ====================

export interface OrderFlowLevel {
  price: number;
  bidVolume: number;
  askVolume: number;
  totalVolume: number;
  delta: number;
}

export interface FootprintLevel extends OrderFlowLevel {
  isDominant: 'bid' | 'ask' | 'neutral';
  isPOC: boolean;
  imbalanceRatio?: number;
}

export interface FootprintCandle {
  time_interval: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  delta: number;
  oflow_detail: Record<string, { asks: number; bids: number }>;  // 0.25 tick granularity
  oflow_unit: Record<string, { asks: number; bids: number }>;    // 1.0 point granularity
  real_poc: number;
  real_poc_volume: number;
  real_poc_percentage: number;
  asellers_uwick: number;
  asellers_lwick: number;
  abuyers_uwick: number;
  abuyers_lwick: number;
}

// ==================== Volume Profile Types ====================

export interface VolumeProfileLevel {
  price: number;
  volume: number;
  buyVolume: number;
  sellVolume: number;
}

export interface VolumeProfile {
  levels: VolumeProfileLevel[];
  poc: number;          // Point of Control
  vah: number;          // Value Area High
  val: number;          // Value Area Low
  totalVolume: number;
  valueAreaVolume: number;
}

// ==================== Visualization Types ====================

export type VisualizationMode = 'candles' | 'hybrid' | 'footprint';

export interface VisualizationState {
  mode: VisualizationMode;
  showVolumeProfile: boolean;
  showFootprint: boolean;
  visibleBars: number;
  zoomLevel: number;
}

// ==================== Chart Configuration ====================

export interface ChartColorScheme {
  bullish: string;
  bearish: string;
  neutral: string;
  background: string;
  grid: string;
  text: string;
  pocBorder: string;
}

export const DEFAULT_COLOR_SCHEME: ChartColorScheme = {
  bullish: '#26a69a',
  bearish: '#ef5350',
  neutral: '#2196f3',
  background: '#0b1523',
  grid: '#1e2837',
  text: '#d1d4dc',
  pocBorder: '#000000',
};

// ==================== API Response Types ====================

export interface CandlesAPIResponse {
  data: OHLCVCandle[];
  total: number;
  start_datetime: string;
  end_datetime: string;
}

export interface FootprintAPIResponse {
  data: FootprintCandle[];
  total: number;
}

// ==================== Utility Types ====================

export interface PriceRange {
  min: number;
  max: number;
  tickSize: number;
}

export interface TimeRange {
  start: Date;
  end: Date;
}

// ==================== Render Data Types ====================

export interface FootprintRenderData {
  candle: FootprintCandle;
  levels: FootprintLevel[];
  poc: FootprintLevel;
  deltaTotal: number;
  volumeTotal: number;
}

export interface VolumeProfileRenderData {
  profile: VolumeProfile;
  maxVolume: number;
  priceRange: PriceRange;
}
