/**
 * Feature Engineering Types
 */

export interface Indicator {
  id: string;
  name: string;
  category: 'momentum' | 'trend' | 'volatility' | 'volume' | 'orderflow';
  parameters: Record<string, number>;
  description?: string;
}

export interface FeatureSet {
  id: string;
  name: string;
  indicators: Indicator[];
  created_at: string;
  updated_at: string;
}

export interface CalculateIndicatorRequest {
  indicator_id: string;
  symbol: string;
  timeframe: string;
  period: number;
  parameters?: Record<string, number>;
}

export interface CalculateIndicatorResponse {
  indicator_id: string;
  values: Array<{
    timestamp: string;
    value: number;
  }>;
  metadata: {
    calculation_time_ms: number;
    data_points: number;
  };
}