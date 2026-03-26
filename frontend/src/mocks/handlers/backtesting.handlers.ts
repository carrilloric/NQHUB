/**
 * Backtesting API Mock Handlers
 */

import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const backtestingHandlers = [
  // Run backtest
  http.post(`${API_BASE}/backtesting/run`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json({
      id: 'backtest-' + Date.now(),
      strategy_id: body.strategy_id,
      status: 'pending',
      start_date: body.start_date,
      end_date: body.end_date,
      symbol: body.symbol,
      timeframe: body.timeframe,
      created_at: new Date().toISOString(),
    });
  }),

  // Get backtest runs
  http.get(`${API_BASE}/backtesting/runs`, () => {
    return HttpResponse.json([]);
  }),

  // Get specific run
  http.get(`${API_BASE}/backtesting/run/:id`, ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      status: 'completed',
      results: {
        total_trades: 100,
        winning_trades: 60,
        losing_trades: 40,
        win_rate: 0.6,
        profit_factor: 1.5,
        sharpe_ratio: 1.2,
        max_drawdown: -0.15,
        total_pnl: 5000,
        average_win: 150,
        average_loss: -75,
        trades: [],
        equity_curve: [],
      },
    });
  }),
];