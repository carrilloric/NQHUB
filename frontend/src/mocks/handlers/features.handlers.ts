/**
 * Features API Mock Handlers
 */

import { http, HttpResponse } from 'msw';
import type { Indicator, FeatureSet } from '@shared/types/features.types';

const API_BASE = '/api/v1';

// Mock data
const mockIndicators: Indicator[] = [
  {
    id: 'rsi',
    name: 'RSI',
    category: 'momentum',
    parameters: { period: 14 },
    description: 'Relative Strength Index',
  },
  {
    id: 'macd',
    name: 'MACD',
    category: 'trend',
    parameters: { fast: 12, slow: 26, signal: 9 },
    description: 'Moving Average Convergence Divergence',
  },
  {
    id: 'bb',
    name: 'Bollinger Bands',
    category: 'volatility',
    parameters: { period: 20, stdDev: 2 },
    description: 'Bollinger Bands indicator',
  },
];

const mockFeatureSets: FeatureSet[] = [
  {
    id: '1',
    name: 'Momentum Strategy Features',
    indicators: [mockIndicators[0], mockIndicators[1]],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

export const featuresHandlers = [
  // Get all indicators
  http.get(`${API_BASE}/features/indicators`, () => {
    return HttpResponse.json(mockIndicators);
  }),

  // Calculate indicator
  http.post(`${API_BASE}/features/calculate`, async ({ request }) => {
    const body = await request.json() as any;

    // Generate mock values
    const values = Array.from({ length: 100 }, (_, i) => ({
      timestamp: new Date(Date.now() - i * 60000).toISOString(),
      value: Math.random() * 100,
    }));

    return HttpResponse.json({
      indicator_id: body.indicator_id,
      values,
      metadata: {
        calculation_time_ms: Math.random() * 100,
        data_points: values.length,
      },
    });
  }),

  // Get feature sets
  http.get(`${API_BASE}/features/feature-sets`, () => {
    return HttpResponse.json(mockFeatureSets);
  }),

  // Create feature set
  http.post(`${API_BASE}/features/feature-sets`, async ({ request }) => {
    const body = await request.json() as any;

    const newFeatureSet: FeatureSet = {
      id: String(mockFeatureSets.length + 1),
      name: body.name,
      indicators: body.indicator_ids.map((id: string) =>
        mockIndicators.find(ind => ind.id === id)
      ).filter(Boolean),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockFeatureSets.push(newFeatureSet);
    return HttpResponse.json(newFeatureSet);
  }),
];