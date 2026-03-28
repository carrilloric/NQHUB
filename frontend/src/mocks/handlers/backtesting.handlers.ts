/**
 * Backtesting API Mock Handlers
 * Based on CONTRACT-003 specifications
 */

import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

// Mock data stores
let mockStrategies = [
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    name: 'Moving Average Crossover',
    type: 'mean_reversion',
    version: '1.0.0',
    status: 'active',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-03-15T14:30:00Z',
    description: 'Classic MA crossover strategy with 20/50 periods',
    tags: ['MA', 'trend-following'],
    config: {
      short_period: 20,
      long_period: 50,
      position_size: 1,
      stop_loss: 0.02
    },
    metrics: {
      total_runs: 12,
      avg_sharpe: 1.45,
      avg_win_rate: 0.58,
      best_profit_factor: 1.8
    }
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440002',
    name: 'RSI Divergence',
    type: 'momentum',
    version: '2.1.0',
    status: 'active',
    created_at: '2024-02-01T09:00:00Z',
    updated_at: '2024-03-20T11:15:00Z',
    description: 'RSI divergence detection with dynamic thresholds',
    tags: ['RSI', 'divergence', 'momentum'],
    config: {
      rsi_period: 14,
      overbought: 70,
      oversold: 30,
      divergence_threshold: 5
    },
    metrics: {
      total_runs: 8,
      avg_sharpe: 1.2,
      avg_win_rate: 0.52,
      best_profit_factor: 1.5
    }
  }
];

let mockBacktestRuns = [
  {
    id: '660e8400-e29b-41d4-a716-446655440010',
    strategy_id: '550e8400-e29b-41d4-a716-446655440001',
    strategy_name: 'Moving Average Crossover',
    status: 'completed',
    start_date: '2024-01-01',
    end_date: '2024-03-01',
    symbol: 'NQ',
    timeframe: '1h',
    created_at: '2024-03-20T10:00:00Z',
    completed_at: '2024-03-20T10:05:00Z',
    duration_seconds: 300,
    config: {
      short_period: 20,
      long_period: 50
    },
    results: {
      sharpe: 1.5,
      profit_factor: 1.6,
      total_trades: 150,
      winning_trades: 87,
      losing_trades: 63,
      win_rate: 0.58,
      max_dd: -0.12,
      total_pnl: 15000,
      avg_win: 250,
      avg_loss: -150,
      best_trade: 1200,
      worst_trade: -800,
      max_consecutive_wins: 8,
      max_consecutive_losses: 5,
      equity_curve: generateEquityCurve(150),
      trades: generateMockTrades(20)
    }
  },
  {
    id: '660e8400-e29b-41d4-a716-446655440011',
    strategy_id: '550e8400-e29b-41d4-a716-446655440002',
    strategy_name: 'RSI Divergence',
    status: 'completed',
    start_date: '2024-01-01',
    end_date: '2024-03-01',
    symbol: 'NQ',
    timeframe: '15m',
    created_at: '2024-03-19T14:00:00Z',
    completed_at: '2024-03-19T14:03:00Z',
    duration_seconds: 180,
    config: {
      rsi_period: 14,
      divergence_threshold: 5
    },
    results: {
      sharpe: 1.2,
      profit_factor: 1.3,
      total_trades: 89,
      winning_trades: 46,
      losing_trades: 43,
      win_rate: 0.52,
      max_dd: -0.15,
      total_pnl: 8500,
      avg_win: 320,
      avg_loss: -180,
      best_trade: 1500,
      worst_trade: -900,
      max_consecutive_wins: 6,
      max_consecutive_losses: 4,
      equity_curve: generateEquityCurve(89),
      trades: generateMockTrades(15)
    }
  }
];

// Helper functions
function generateEquityCurve(points: number) {
  const curve = [];
  let balance = 100000;
  const now = new Date();

  for (let i = 0; i < points; i++) {
    const timestamp = new Date(now.getTime() - (points - i) * 3600000);
    const change = (Math.random() - 0.45) * 1000; // Slight positive bias
    balance += change;
    curve.push({
      timestamp: timestamp.toISOString(),
      balance: Math.round(balance * 100) / 100,
      drawdown: Math.random() > 0.7 ? -(Math.random() * 5) : 0
    });
  }

  return curve;
}

function generateMockTrades(count: number) {
  const trades = [];
  const symbols = ['NQ'];
  const now = new Date();

  for (let i = 0; i < count; i++) {
    const entryTime = new Date(now.getTime() - (count - i) * 7200000);
    const exitTime = new Date(entryTime.getTime() + Math.random() * 3600000);
    const isWin = Math.random() > 0.42;

    trades.push({
      id: `trade-${i + 1}`,
      symbol: symbols[0],
      side: Math.random() > 0.5 ? 'long' : 'short',
      entry_time: entryTime.toISOString(),
      exit_time: exitTime.toISOString(),
      entry_price: 15000 + Math.random() * 500,
      exit_price: 15000 + Math.random() * 500,
      quantity: Math.ceil(Math.random() * 5),
      pnl: isWin ? Math.random() * 500 : -Math.random() * 300,
      pnl_percent: isWin ? Math.random() * 3 : -Math.random() * 2,
      commission: 2.5,
      slippage: 0.5,
      tags: isWin ? ['winner'] : ['loser']
    });
  }

  return trades;
}

export const backtestingHandlers = [
  // ==================== STRATEGIES ====================

  // List strategies
  http.get(`${API_BASE}/backtest/strategies`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const type = url.searchParams.get('type');

    let filtered = [...mockStrategies];

    if (status) {
      filtered = filtered.filter(s => s.status === status);
    }

    if (type) {
      filtered = filtered.filter(s => s.type === type);
    }

    return HttpResponse.json({
      strategies: filtered,
      total: filtered.length
    });
  }),

  // Get strategy source code
  http.get(`${API_BASE}/backtest/strategies/:id/source`, ({ params }) => {
    const strategy = mockStrategies.find(s => s.id === params.id);

    if (!strategy) {
      return HttpResponse.json(
        { detail: 'Strategy not found' },
        { status: 404 }
      );
    }

    const mockCode = `"""
${strategy.name} Strategy
Version: ${strategy.version}
"""

import pandas as pd
import numpy as np

def initialize(context):
    """Initialize strategy parameters"""
    context.symbol = 'NQ'
    context.short_period = ${strategy.config.short_period || 20}
    context.long_period = ${strategy.config.long_period || 50}

def handle_data(context, data):
    """Main strategy logic"""
    # Calculate moving averages
    prices = data.history(context.symbol, 'price', context.long_period, '1d')
    short_ma = prices[-context.short_period:].mean()
    long_ma = prices.mean()

    # Generate signals
    if short_ma > long_ma:
        order_target_percent(context.symbol, 1.0)
    elif short_ma < long_ma:
        order_target_percent(context.symbol, 0.0)

def analyze(context, results):
    """Post-processing and analysis"""
    return results
`;

    return HttpResponse.json({
      id: params.id,
      name: strategy.name,
      version: strategy.version,
      code: mockCode,
      language: 'python',
      created_at: strategy.created_at,
      updated_at: strategy.updated_at
    });
  }),

  // Validate strategy
  http.post(`${API_BASE}/backtest/strategies/validate`, async ({ request }) => {
    const body = await request.json() as any;

    // Simulate validation
    const hasInitialize = body.code.includes('def initialize');
    const hasHandleData = body.code.includes('def handle_data');

    const errors = [];
    const warnings = [];

    if (!hasInitialize) {
      errors.push('Missing required function: initialize(context)');
    }

    if (!hasHandleData) {
      errors.push('Missing required function: handle_data(context, data)');
    }

    if (!body.code.includes('import')) {
      warnings.push('Consider importing required libraries (pandas, numpy)');
    }

    return HttpResponse.json({
      valid: errors.length === 0,
      errors,
      warnings,
      detected_name: body.name || 'Untitled Strategy',
      detected_type: 'trend_following',
      required_features: ['price_data', 'indicators']
    });
  }),

  // Save strategy
  http.post(`${API_BASE}/backtest/strategies/save`, async ({ request }) => {
    const body = await request.json() as any;

    if (body.id) {
      // Update existing
      const index = mockStrategies.findIndex(s => s.id === body.id);
      if (index !== -1) {
        mockStrategies[index] = {
          ...mockStrategies[index],
          ...body,
          updated_at: new Date().toISOString()
        };
        return HttpResponse.json(mockStrategies[index]);
      }
    }

    // Create new
    const newStrategy = {
      id: `550e8400-e29b-41d4-a716-${Date.now()}`,
      name: body.name,
      type: body.type || 'custom',
      version: '1.0.0',
      status: 'active',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      description: body.description || '',
      tags: body.tags || [],
      config: body.config || {},
      metrics: {
        total_runs: 0,
        avg_sharpe: 0,
        avg_win_rate: 0,
        best_profit_factor: 0
      }
    };

    mockStrategies.push(newStrategy);
    return HttpResponse.json(newStrategy, { status: 201 });
  }),

  // ==================== BACKTESTS ====================

  // Run backtest
  http.post(`${API_BASE}/backtest/run`, async ({ request }) => {
    const body = await request.json() as any;

    const strategy = mockStrategies.find(s => s.id === body.strategy_id);
    if (!strategy) {
      return HttpResponse.json(
        { detail: 'Strategy not found' },
        { status: 404 }
      );
    }

    const newRun = {
      id: `660e8400-e29b-41d4-a716-${Date.now()}`,
      strategy_id: body.strategy_id,
      strategy_name: strategy.name,
      status: 'pending',
      start_date: body.start_date,
      end_date: body.end_date,
      symbol: body.symbol || 'NQ',
      timeframe: body.timeframe || '1h',
      created_at: new Date().toISOString(),
      config: body.parameters || strategy.config
    };

    mockBacktestRuns.push(newRun as any);

    // Simulate completion after a delay
    setTimeout(() => {
      const run = mockBacktestRuns.find(r => r.id === newRun.id);
      if (run) {
        run.status = 'completed';
        run.completed_at = new Date().toISOString();
        run.duration_seconds = 180;
        run.results = {
          sharpe: 1.3 + Math.random() * 0.4,
          profit_factor: 1.4 + Math.random() * 0.3,
          total_trades: Math.floor(100 + Math.random() * 100),
          winning_trades: Math.floor(50 + Math.random() * 50),
          losing_trades: Math.floor(30 + Math.random() * 30),
          win_rate: 0.5 + Math.random() * 0.15,
          max_dd: -(0.1 + Math.random() * 0.1),
          total_pnl: 10000 + Math.random() * 10000,
          avg_win: 200 + Math.random() * 100,
          avg_loss: -(100 + Math.random() * 50),
          best_trade: 1000 + Math.random() * 500,
          worst_trade: -(500 + Math.random() * 300),
          max_consecutive_wins: Math.floor(5 + Math.random() * 5),
          max_consecutive_losses: Math.floor(3 + Math.random() * 3),
          equity_curve: generateEquityCurve(100),
          trades: generateMockTrades(20)
        };
      }
    }, 3000);

    return HttpResponse.json(newRun, { status: 202 });
  }),

  // Import backtest results
  http.post(`${API_BASE}/backtest/results/import`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json({
      message: 'Results imported successfully',
      run_id: `660e8400-e29b-41d4-a716-${Date.now()}`,
      imported_trades: body.trades?.length || 0,
      imported_metrics: Object.keys(body.metrics || {}).length
    });
  }),

  // List backtest runs
  http.get(`${API_BASE}/backtest/runs`, ({ request }) => {
    const url = new URL(request.url);
    const strategyId = url.searchParams.get('strategy_id');
    const status = url.searchParams.get('status');

    let filtered = [...mockBacktestRuns];

    if (strategyId) {
      filtered = filtered.filter(r => r.strategy_id === strategyId);
    }

    if (status) {
      filtered = filtered.filter(r => r.status === status);
    }

    return HttpResponse.json({
      runs: filtered,
      total: filtered.length
    });
  }),

  // Get specific backtest run
  http.get(`${API_BASE}/backtest/runs/:id`, ({ params }) => {
    const run = mockBacktestRuns.find(r => r.id === params.id);

    if (!run) {
      return HttpResponse.json(
        { detail: 'Backtest run not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(run);
  }),

  // Screener (filter backtests)
  http.get(`${API_BASE}/backtest/screener`, ({ request }) => {
    const url = new URL(request.url);
    const minSharpe = parseFloat(url.searchParams.get('min_sharpe') || '0');
    const minWinRate = parseFloat(url.searchParams.get('min_win_rate') || '0');

    const filtered = mockBacktestRuns.filter(r => {
      if (!r.results) return false;
      return r.results.sharpe >= minSharpe && r.results.win_rate >= minWinRate;
    });

    return HttpResponse.json({
      runs: filtered,
      total: filtered.length,
      filters_applied: {
        min_sharpe: minSharpe,
        min_win_rate: minWinRate
      }
    });
  }),

  // Optimize strategy
  http.post(`${API_BASE}/backtest/optimize`, async ({ request }) => {
    const body = await request.json() as any;

    // Simulate optimization results
    const combinations = [];
    for (let i = 0; i < 10; i++) {
      combinations.push({
        parameters: {
          short_period: 10 + i * 5,
          long_period: 30 + i * 10
        },
        metrics: {
          sharpe: 1.0 + Math.random() * 0.8,
          profit_factor: 1.2 + Math.random() * 0.5,
          win_rate: 0.45 + Math.random() * 0.2,
          max_dd: -(0.08 + Math.random() * 0.12),
          total_pnl: 5000 + Math.random() * 15000
        }
      });
    }

    // Sort by sharpe ratio
    combinations.sort((a, b) => b.metrics.sharpe - a.metrics.sharpe);

    return HttpResponse.json({
      optimization_id: `opt-${Date.now()}`,
      strategy_id: body.strategy_id,
      status: 'completed',
      total_combinations: combinations.length,
      best_combination: combinations[0],
      all_results: combinations
    });
  }),

  // ==================== APPROVAL ====================

  // Get approval checklist
  http.get(`${API_BASE}/backtest/approval/checklist/:strategyId`, ({ params }) => {
    const strategy = mockStrategies.find(s => s.id === params.strategyId);

    if (!strategy) {
      return HttpResponse.json(
        { detail: 'Strategy not found' },
        { status: 404 }
      );
    }

    // Get latest run for this strategy
    const latestRun = mockBacktestRuns
      .filter(r => r.strategy_id === params.strategyId && r.status === 'completed')
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

    if (!latestRun || !latestRun.results) {
      return HttpResponse.json({
        strategy_id: params.strategyId,
        approved: false,
        checks: {
          has_backtest: false,
          sharpe_threshold: false,
          profit_factor_threshold: false,
          trade_count_threshold: false,
          drawdown_threshold: false
        },
        thresholds: {
          min_sharpe: 1.5,
          min_profit_factor: 1.5,
          min_trades: 100,
          max_drawdown: 0.30
        },
        message: 'No completed backtest found for approval'
      });
    }

    const checks = {
      has_backtest: true,
      sharpe_threshold: latestRun.results.sharpe >= 1.5,
      profit_factor_threshold: latestRun.results.profit_factor >= 1.5,
      trade_count_threshold: latestRun.results.total_trades >= 100,
      drawdown_threshold: Math.abs(latestRun.results.max_dd) <= 0.30
    };

    const approved = Object.values(checks).every(check => check);

    return HttpResponse.json({
      strategy_id: params.strategyId,
      approved,
      checks,
      thresholds: {
        min_sharpe: 1.5,
        min_profit_factor: 1.5,
        min_trades: 100,
        max_drawdown: 0.30
      },
      latest_run: {
        id: latestRun.id,
        sharpe: latestRun.results.sharpe,
        profit_factor: latestRun.results.profit_factor,
        total_trades: latestRun.results.total_trades,
        max_drawdown: latestRun.results.max_dd,
        created_at: latestRun.created_at
      },
      message: approved ? 'Strategy meets all approval criteria' : 'Strategy does not meet all approval criteria'
    });
  }),

  // Approve strategy
  http.post(`${API_BASE}/backtest/approval/approve`, async ({ request }) => {
    const body = await request.json() as any;

    const strategy = mockStrategies.find(s => s.id === body.strategy_id);
    if (!strategy) {
      return HttpResponse.json(
        { detail: 'Strategy not found' },
        { status: 404 }
      );
    }

    // Update strategy status
    strategy.status = 'approved';

    return HttpResponse.json({
      strategy_id: body.strategy_id,
      status: 'approved',
      approved_at: new Date().toISOString(),
      approved_by: 'test-user',
      notes: body.notes || 'Strategy approved for production'
    });
  }),
];