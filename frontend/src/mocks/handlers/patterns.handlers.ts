/**
 * Pattern Detection API Mock Handlers
 * Based on CONTRACT-002 specification
 */

import { http, HttpResponse } from 'msw';
import type {
  FVGPattern,
  OrderBlockPattern,
  LiquidityPoolPattern,
  MarketStateSnapshot,
  PatternInteraction,
  PaginatedResponse,
  PaginatedInteractionResponse,
} from '@shared/types/patterns.types';

const API_BASE = '/api/v1/patterns';

// Helper function to generate mock timestamps
const generateTimestamps = (count: number, startDate: Date = new Date()) => {
  return Array.from({ length: count }, (_, i) => {
    const date = new Date(startDate);
    date.setMinutes(date.getMinutes() - i * 5);
    return date.toISOString();
  });
};

// Mock FVG data
const generateMockFVGs = (count: number = 20): FVGPattern[] => {
  const timestamps = generateTimestamps(count);
  const significances = ['MICRO', 'SMALL', 'MEDIUM', 'LARGE', 'EXTREME'] as const;
  const statuses = ['UNMITIGATED', 'REDELIVERED', 'REBALANCED'] as const;
  const directions = ['BULLISH', 'BEARISH'] as const;

  return timestamps.map((timestamp, i) => {
    const basePrice = 20000 + Math.random() * 1000;
    const gapSize = 5 + Math.random() * 50;
    const isBullish = Math.random() > 0.5;

    return {
      id: i + 1,
      symbol: 'NQH25',
      timeframe: '5min' as const,
      formation_time: timestamp,
      gap_high: basePrice + (isBullish ? gapSize : 0),
      gap_low: basePrice - (isBullish ? 0 : gapSize),
      gap_size_pts: gapSize,
      gap_size_pct: (gapSize / basePrice) * 100,
      significance: significances[Math.floor(Math.random() * significances.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      direction: directions[Math.floor(Math.random() * directions.length)],
      premium_level: basePrice + gapSize * 0.75,
      discount_level: basePrice - gapSize * 0.25,
      consequent_encroachment: basePrice + gapSize * 0.5,
      displacement_score: 0.5 + Math.random() * 0.5,
      has_break_of_structure: Math.random() > 0.6,
      mitigation_time: Math.random() > 0.7 ? timestamps[Math.max(0, i - 1)] : null,
      mitigation_candle_id: Math.random() > 0.7 ? Math.floor(Math.random() * 1000) : null,
    };
  });
};

// Mock Order Block data
const generateMockOrderBlocks = (count: number = 20): OrderBlockPattern[] => {
  const timestamps = generateTimestamps(count);
  const types = ['BULLISH OB', 'BEARISH OB', 'STRONG BULLISH OB', 'STRONG BEARISH OB'] as const;
  const qualities = ['HIGH', 'MEDIUM', 'LOW'] as const;
  const statuses = ['ACTIVE', 'TESTED', 'BROKEN'] as const;
  const impulseDirections = ['UP', 'DOWN'] as const;

  return timestamps.map((timestamp, i) => {
    const basePrice = 20000 + Math.random() * 1000;
    const obRange = 10 + Math.random() * 30;
    const isBullish = types[Math.floor(Math.random() * types.length)].includes('BULLISH');

    return {
      id: i + 1,
      symbol: 'NQH25',
      timeframe: '5min' as const,
      formation_time: timestamp,
      ob_high: basePrice + obRange,
      ob_low: basePrice,
      ob_type: types[Math.floor(Math.random() * types.length)],
      quality: qualities[Math.floor(Math.random() * qualities.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      ob_body_midpoint: basePrice + obRange * 0.5,
      ob_range_midpoint: basePrice + obRange * 0.5,
      impulse_move: 20 + Math.random() * 80,
      impulse_direction: isBullish ? 'UP' : 'DOWN',
      volume: Math.floor(1000 + Math.random() * 10000),
      test_time: Math.random() > 0.6 ? timestamps[Math.max(0, i - 1)] : null,
      break_time: Math.random() > 0.8 ? timestamps[Math.max(0, i - 1)] : null,
    };
  });
};

// Mock Liquidity Pool data
const generateMockLiquidityPools = (count: number = 20): LiquidityPoolPattern[] => {
  const timestamps = generateTimestamps(count);
  const poolTypes = ['EQH', 'EQL', 'NYH', 'NYL', 'ASH', 'ASL', 'LSH', 'LSL', 'SWING_HIGH', 'SWING_LOW'] as const;
  const strengths = ['STRONG', 'NORMAL', 'WEAK'] as const;
  const statuses = ['UNMITIGATED', 'RESPECTED', 'SWEPT', 'MITIGATED'] as const;

  return timestamps.map((timestamp, i) => {
    const basePrice = 20000 + Math.random() * 1000;
    const zoneHeight = 5 + Math.random() * 20;

    return {
      id: i + 1,
      symbol: 'NQH25',
      timeframe: '5min' as const,
      formation_time: timestamp,
      zone_high: basePrice + zoneHeight,
      zone_low: basePrice,
      pool_type: poolTypes[Math.floor(Math.random() * poolTypes.length)],
      strength: strengths[Math.floor(Math.random() * strengths.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      modal_level: basePrice + zoneHeight * 0.5,
      touches: Math.floor(2 + Math.random() * 8),
      sweep_time: Math.random() > 0.7 ? timestamps[Math.max(0, i - 1)] : null,
      mitigation_time: Math.random() > 0.8 ? timestamps[Math.max(0, i - 1)] : null,
    };
  });
};

// Mock Pattern Interactions
const generateMockInteractions = (count: number = 30): PatternInteraction[] => {
  const timestamps = generateTimestamps(count);
  const patternTypes = ['FVG', 'OB', 'LP'] as const;
  const interactionTypes = ['R0', 'R1', 'R2', 'R3', 'R4', 'P1', 'P2', 'P3', 'P4', 'P5'] as const;

  return timestamps.map((timestamp, i) => {
    const basePrice = 20000 + Math.random() * 1000;

    return {
      id: i + 1,
      pattern_type: patternTypes[Math.floor(Math.random() * patternTypes.length)],
      pattern_id: Math.floor(1 + Math.random() * 20),
      interaction_time: timestamp,
      interaction_type: interactionTypes[Math.floor(Math.random() * interactionTypes.length)],
      penetration_pts: Math.random() * 50,
      penetration_pct: Math.random() * 100,
      candle_high: basePrice + Math.random() * 20,
      candle_low: basePrice - Math.random() * 20,
      candle_close: basePrice + (Math.random() - 0.5) * 10,
      volume: Math.floor(1000 + Math.random() * 10000),
      confidence: 0.5 + Math.random() * 0.5,
    };
  });
};

// Pre-generate mock data
let mockFVGs = generateMockFVGs(50);
let mockOrderBlocks = generateMockOrderBlocks(50);
let mockLiquidityPools = generateMockLiquidityPools(50);
let mockInteractions = generateMockInteractions(100);

// Helper function for pagination
function paginate<T>(items: T[], page: number = 1, pageSize: number = 50): PaginatedResponse<T> {
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedItems = items.slice(startIndex, endIndex);

  return {
    data: paginatedItems,
    total: items.length,
    page,
    page_size: pageSize,
    has_more: endIndex < items.length,
  };
}

export const patternsHandlers = [
  // Fair Value Gaps endpoint
  http.get(`${API_BASE}/fvgs`, ({ request }) => {
    const url = new URL(request.url);
    const params = Object.fromEntries(url.searchParams);

    let filtered = [...mockFVGs];

    // Apply filters
    if (params.symbol) {
      filtered = filtered.filter(f => f.symbol === params.symbol);
    }
    if (params.timeframe) {
      filtered = filtered.filter(f => f.timeframe === params.timeframe);
    }
    if (params.status) {
      filtered = filtered.filter(f => f.status === params.status);
    }
    if (params.significance) {
      filtered = filtered.filter(f => f.significance === params.significance);
    }
    if (params.start_date) {
      const startDate = new Date(params.start_date);
      filtered = filtered.filter(f => new Date(f.formation_time) >= startDate);
    }
    if (params.end_date) {
      const endDate = new Date(params.end_date);
      filtered = filtered.filter(f => new Date(f.formation_time) <= endDate);
    }

    // Sort
    const sortBy = params.sort_by || 'formation_time';
    const sortOrder = params.sort_order || 'desc';
    filtered.sort((a: any, b: any) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      return sortOrder === 'asc' ?
        (aVal > bVal ? 1 : -1) :
        (bVal > aVal ? 1 : -1);
    });

    // Paginate
    const page = parseInt(params.page || '1');
    const pageSize = parseInt(params.page_size || '50');

    return HttpResponse.json(paginate(filtered, page, pageSize));
  }),

  // Order Blocks endpoint
  http.get(`${API_BASE}/order-blocks`, ({ request }) => {
    const url = new URL(request.url);
    const params = Object.fromEntries(url.searchParams);

    let filtered = [...mockOrderBlocks];

    // Apply filters
    if (params.symbol) {
      filtered = filtered.filter(ob => ob.symbol === params.symbol);
    }
    if (params.timeframe) {
      filtered = filtered.filter(ob => ob.timeframe === params.timeframe);
    }
    if (params.status) {
      filtered = filtered.filter(ob => ob.status === params.status);
    }
    if (params.ob_type) {
      filtered = filtered.filter(ob => ob.ob_type === params.ob_type);
    }
    if (params.quality) {
      filtered = filtered.filter(ob => ob.quality === params.quality);
    }
    if (params.start_date) {
      const startDate = new Date(params.start_date);
      filtered = filtered.filter(ob => new Date(ob.formation_time) >= startDate);
    }
    if (params.end_date) {
      const endDate = new Date(params.end_date);
      filtered = filtered.filter(ob => new Date(ob.formation_time) <= endDate);
    }

    // Sort
    const sortBy = params.sort_by || 'formation_time';
    const sortOrder = params.sort_order || 'desc';
    filtered.sort((a: any, b: any) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      return sortOrder === 'asc' ?
        (aVal > bVal ? 1 : -1) :
        (bVal > aVal ? 1 : -1);
    });

    // Paginate
    const page = parseInt(params.page || '1');
    const pageSize = parseInt(params.page_size || '50');

    return HttpResponse.json(paginate(filtered, page, pageSize));
  }),

  // Liquidity Pools endpoint
  http.get(`${API_BASE}/liquidity-pools`, ({ request }) => {
    const url = new URL(request.url);
    const params = Object.fromEntries(url.searchParams);

    let filtered = [...mockLiquidityPools];

    // Apply filters
    if (params.symbol) {
      filtered = filtered.filter(lp => lp.symbol === params.symbol);
    }
    if (params.timeframe) {
      filtered = filtered.filter(lp => lp.timeframe === params.timeframe);
    }
    if (params.status) {
      filtered = filtered.filter(lp => lp.status === params.status);
    }
    if (params.pool_type) {
      filtered = filtered.filter(lp => lp.pool_type === params.pool_type);
    }
    if (params.strength) {
      filtered = filtered.filter(lp => lp.strength === params.strength);
    }
    if (params.start_date) {
      const startDate = new Date(params.start_date);
      filtered = filtered.filter(lp => new Date(lp.formation_time) >= startDate);
    }
    if (params.end_date) {
      const endDate = new Date(params.end_date);
      filtered = filtered.filter(lp => new Date(lp.formation_time) <= endDate);
    }

    // Sort
    const sortBy = params.sort_by || 'formation_time';
    const sortOrder = params.sort_order || 'desc';
    filtered.sort((a: any, b: any) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      return sortOrder === 'asc' ?
        (aVal > bVal ? 1 : -1) :
        (bVal > aVal ? 1 : -1);
    });

    // Paginate
    const page = parseInt(params.page || '1');
    const pageSize = parseInt(params.page_size || '50');

    return HttpResponse.json(paginate(filtered, page, pageSize));
  }),

  // Market State endpoint
  http.get(`${API_BASE}/market-state`, ({ request }) => {
    const url = new URL(request.url);
    const params = Object.fromEntries(url.searchParams);

    const currentPrice = 20000 + Math.random() * 500;

    const snapshot: MarketStateSnapshot = {
      timestamp: new Date().toISOString(),
      symbol: params.symbol || 'NQH25',
      timeframe: (params.timeframe || '5min') as any,
      current_price: currentPrice,
      active_patterns: {
        fvgs: mockFVGs.slice(0, 5).map(f => ({
          id: f.id,
          gap_high: f.gap_high,
          gap_low: f.gap_low,
          significance: f.significance,
        })),
        order_blocks: mockOrderBlocks.slice(0, 5).map(ob => ({
          id: ob.id,
          ob_high: ob.ob_high,
          ob_low: ob.ob_low,
          ob_type: ob.ob_type,
        })),
        liquidity_pools: mockLiquidityPools.slice(0, 5).map(lp => ({
          id: lp.id,
          zone_high: lp.zone_high,
          zone_low: lp.zone_low,
          pool_type: lp.pool_type,
        })),
      },
      summary: {
        total_active_fvgs: mockFVGs.filter(f => f.status === 'UNMITIGATED').length,
        total_active_obs: mockOrderBlocks.filter(ob => ob.status === 'ACTIVE').length,
        total_active_lps: mockLiquidityPools.filter(lp => lp.status === 'UNMITIGATED').length,
        nearest_resistance: currentPrice + 50,
        nearest_support: currentPrice - 50,
      },
    };

    return HttpResponse.json(snapshot);
  }),

  // Pattern Interactions endpoint
  http.get(`${API_BASE}/interactions`, ({ request }) => {
    const url = new URL(request.url);
    const params = Object.fromEntries(url.searchParams);

    let filtered = [...mockInteractions];

    // Apply filters
    if (params.pattern_type) {
      filtered = filtered.filter(i => i.pattern_type === params.pattern_type);
    }
    if (params.pattern_id) {
      filtered = filtered.filter(i => i.pattern_id === parseInt(params.pattern_id));
    }
    if (params.interaction_type) {
      filtered = filtered.filter(i => i.interaction_type === params.interaction_type);
    }
    if (params.start_date) {
      const startDate = new Date(params.start_date);
      filtered = filtered.filter(i => new Date(i.interaction_time) >= startDate);
    }
    if (params.end_date) {
      const endDate = new Date(params.end_date);
      filtered = filtered.filter(i => new Date(i.interaction_time) <= endDate);
    }

    // Paginate
    const page = parseInt(params.page || '1');
    const pageSize = parseInt(params.page_size || '50');
    const paginated = paginate(filtered, page, pageSize);

    // Add summary for interactions
    const response: PaginatedInteractionResponse = {
      ...paginated,
      summary: {
        by_type: filtered.reduce((acc, interaction) => {
          const type = interaction.interaction_type;
          acc[type] = (acc[type] || 0) + 1;
          return acc;
        }, {} as Record<string, number>),
      },
    };

    return HttpResponse.json(response);
  }),
];