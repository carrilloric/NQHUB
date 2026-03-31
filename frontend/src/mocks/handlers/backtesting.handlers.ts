import { http, HttpResponse } from 'msw';

// Track polling count for simulating async completion
const pollingCounts = new Map<string, number>();

// Generate realistic equity curve data
function generateEquityCurve(initialCapital: number = 25000) {
  const days = 60;
  const curve = [];
  let equity = initialCapital;

  for (let i = 0; i < days; i++) {
    // Simulate realistic P&L with some volatility
    const dailyReturn = (Math.random() - 0.45) * 0.02; // Slight positive bias
    equity = equity * (1 + dailyReturn);
    const drawdown = Math.min(0, (equity - initialCapital) / initialCapital);

    const date = new Date();
    date.setDate(date.getDate() - (days - i));

    curve.push({
      timestamp: date.toISOString(),
      equity: Math.round(equity * 100) / 100,
      drawdown: Math.round(drawdown * 10000) / 10000,
    });
  }

  return curve;
}

// Generate realistic trade data
function generateTrades(count: number = 312) {
  const trades = [];
  let cumulativePnl = 0;

  for (let i = 1; i <= count; i++) {
    const isWin = Math.random() < 0.623; // 62.3% win rate
    const side = Math.random() < 0.5 ? 'LONG' : 'SHORT';
    const entryPrice = 18500 + Math.random() * 500;
    const priceMove = isWin
      ? (Math.random() * 20 + 5) // Win: 5-25 points
      : -(Math.random() * 15 + 3); // Loss: 3-18 points
    const exitPrice = side === 'LONG'
      ? entryPrice + priceMove
      : entryPrice - priceMove;

    const quantity = Math.floor(Math.random() * 3) + 1; // 1-3 contracts
    const pnl = (exitPrice - entryPrice) * quantity * 20 * (side === 'LONG' ? 1 : -1);
    const commission = quantity * 2 * 2.25; // $2.25 per side per contract
    const slippage = quantity * 0.25 * 5 * 2; // 1 tick slippage per side
    const netPnl = pnl - commission - slippage;
    cumulativePnl += netPnl;

    const entryTime = new Date();
    entryTime.setHours(entryTime.getHours() - (count - i) * 2);
    const exitTime = new Date(entryTime);
    exitTime.setMinutes(exitTime.getMinutes() + Math.floor(Math.random() * 60) + 5);

    trades.push({
      trade_id: i,
      entry_time: entryTime.toISOString(),
      exit_time: exitTime.toISOString(),
      side,
      entry_price: Math.round(entryPrice * 4) / 4, // Round to nearest tick
      exit_price: Math.round(exitPrice * 4) / 4,
      quantity,
      pnl: Math.round(pnl * 100) / 100,
      commission: Math.round(commission * 100) / 100,
      slippage: Math.round(slippage * 100) / 100,
      net_pnl: Math.round(netPnl * 100) / 100,
      cumulative_pnl: Math.round(cumulativePnl * 100) / 100,
    });
  }

  return trades;
}

export const backtestingHandlers = [
  // Get available strategies
  http.get('/api/v1/strategies', () => {
    return HttpResponse.json({
      strategies: [
        {
          id: 'fvg-mean-reversion',
          name: 'FVG Mean Reversion',
          description: 'Trade reversals at Fair Value Gaps with ATR-based stops',
        },
        {
          id: 'ob-momentum',
          name: 'Order Block Momentum',
          description: 'Momentum trades from Order Block bounces',
        },
        {
          id: 'lp-sweep-fade',
          name: 'Liquidity Pool Sweep Fade',
          description: 'Fade liquidity sweeps at key levels',
        },
        {
          id: 'nyam-breakout',
          name: 'NY AM Session Breakout',
          description: 'Trade breakouts during NY morning session',
        },
      ],
    });
  }),

  // Run backtest
  http.post('/api/v1/backtest/run', async () => {
    const taskId = `mock-task-${Date.now()}`;
    pollingCounts.set(taskId, 0);

    return HttpResponse.json({
      task_id: taskId,
      status: 'queued',
      message: 'Backtest queued for execution',
    });
  }),

  // Check backtest status
  http.get('/api/v1/backtest/status/:taskId', ({ params }) => {
    const taskId = params.taskId as string;
    const count = pollingCounts.get(taskId) || 0;
    pollingCounts.set(taskId, count + 1);

    // Simulate progress
    if (count < 2) {
      return HttpResponse.json({
        status: 'running',
        progress: 30 + count * 30,
        message: 'Processing historical data...',
      });
    } else {
      // Complete after 2 polls (4 seconds)
      pollingCounts.delete(taskId);
      return HttpResponse.json({
        status: 'completed',
        progress: 100,
        backtest_id: `mock-bt-${Date.now()}`,
        message: 'Backtest completed successfully',
      });
    }
  }),

  // Get backtest results
  http.get('/api/v1/backtest/screener', ({ request }) => {
    const url = new URL(request.url);
    const backtestId = url.searchParams.get('id');

    const equityCurve = generateEquityCurve(25000);
    const finalEquity = equityCurve[equityCurve.length - 1].equity;
    const totalReturn = (finalEquity - 25000) / 25000;

    return HttpResponse.json({
      results: [
        {
          backtest_id: backtestId || 'mock-bt-456',
          strategy_id: 'fvg-mean-reversion',
          strategy_name: 'FVG Mean Reversion',
          status: 'completed',
          metrics: {
            sharpe_ratio: 1.87,
            sortino_ratio: 2.43,
            max_drawdown: -0.042,
            win_rate: 0.623,
            profit_factor: 1.84,
            total_trades: 312,
            total_return: totalReturn,
            annual_return: totalReturn * (252 / 60), // Annualized
            calmar_ratio: (totalReturn * (252 / 60)) / 0.042,
            recovery_factor: totalReturn / 0.042,
          },
          apex_compliance: {
            compliant: true,
            trailing_threshold: {
              value: -1347,
              max_allowed: -1500,
              passed: true,
            },
            max_contracts: {
              value: 3,
              max_allowed: 4,
              passed: true,
            },
            trading_hours: {
              compliant: true,
              violations: [],
            },
            profit_goal: {
              value: 1623,
              target: 1500,
              passed: true,
            },
          },
          equity_curve: equityCurve,
          created_at: new Date(Date.now() - 300000).toISOString(),
          completed_at: new Date().toISOString(),
        },
      ],
    });
  }),

  // Get backtest trades
  http.get('/api/v1/backtest/:backtestId/trades', ({ params, request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '50');

    const allTrades = generateTrades(312);
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const trades = allTrades.slice(start, end);

    return HttpResponse.json({
      trades,
      total: allTrades.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(allTrades.length / pageSize),
    });
  }),

  // Compare multiple backtests
  http.get('/api/v1/backtest/compare', ({ request }) => {
    const url = new URL(request.url);
    const ids = url.searchParams.get('ids')?.split(',') || [];

    const results = ids.map((id, index) => ({
      backtest_id: id,
      strategy_id: ['fvg-mean-reversion', 'ob-momentum', 'lp-sweep-fade'][index % 3],
      strategy_name: ['FVG Mean Reversion', 'Order Block Momentum', 'Liquidity Pool Sweep Fade'][index % 3],
      status: 'completed' as const,
      metrics: {
        sharpe_ratio: 1.87 - index * 0.2,
        sortino_ratio: 2.43 - index * 0.3,
        max_drawdown: -0.042 - index * 0.01,
        win_rate: 0.623 - index * 0.05,
        profit_factor: 1.84 - index * 0.15,
        total_trades: 312 - index * 20,
        total_return: 0.156 - index * 0.02,
        annual_return: 0.624 - index * 0.08,
        calmar_ratio: 14.86 - index * 2,
        recovery_factor: 3.71 - index * 0.5,
      },
      apex_compliance: {
        compliant: index === 0, // First one passes
        trailing_threshold: {
          value: -1347 - index * 200,
          max_allowed: -1500,
          passed: index === 0,
        },
        max_contracts: {
          value: 3 + index,
          max_allowed: 4,
          passed: index < 2,
        },
        trading_hours: {
          compliant: true,
          violations: [],
        },
        profit_goal: {
          value: 1623 - index * 300,
          target: 1500,
          passed: index === 0,
        },
      },
      equity_curve: generateEquityCurve(25000),
      created_at: new Date(Date.now() - 3600000 * (index + 1)).toISOString(),
      completed_at: new Date(Date.now() - 3600000 * index).toISOString(),
    }));

    return HttpResponse.json({ results });
  }),

  // Export backtest data
  http.get('/api/v1/backtest/:backtestId/export', ({ request }) => {
    const url = new URL(request.url);
    const format = url.searchParams.get('format') || 'csv';

    if (format === 'csv') {
      const csv = `trade_id,entry_time,exit_time,side,entry_price,exit_price,quantity,pnl,commission,slippage,net_pnl,cumulative_pnl
1,2024-11-29T09:30:00Z,2024-11-29T09:45:00Z,LONG,18525.50,18530.75,2,210.00,9.00,5.00,196.00,196.00
2,2024-11-29T10:15:00Z,2024-11-29T10:32:00Z,SHORT,18531.25,18528.00,1,65.00,4.50,2.50,58.00,254.00
3,2024-11-29T11:00:00Z,2024-11-29T11:18:00Z,LONG,18527.75,18524.50,3,-195.00,13.50,7.50,-216.00,38.00`;

      return new Response(csv, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': 'attachment; filename="backtest-trades.csv"',
        },
      });
    } else {
      const trades = generateTrades(10);
      return HttpResponse.json({ trades });
    }
  }),
];