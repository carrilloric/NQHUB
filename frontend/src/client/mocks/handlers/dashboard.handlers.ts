/**
 * Dashboard Mock Handlers
 *
 * MSW handlers for Live Dashboard WebSocket and API endpoints
 */
import { http, HttpResponse } from 'msw';
import type { PortfolioSnapshot } from '@/stores/websocketStore';

/**
 * Generate realistic portfolio snapshots for equity curve
 * Creates 50 snapshots over the last 50 minutes with:
 * - Realistic equity fluctuations around $25,000 starting balance
 * - Drawdown calculations
 * - Gradual P&L progression
 */
function generatePortfolioSnapshots(count = 50): PortfolioSnapshot[] {
  const snapshots: PortfolioSnapshot[] = [];
  const startingBalance = 25000;
  let cumulativePnL = 0;

  for (let i = 0; i < count; i++) {
    // Create timestamp (1 minute intervals going back in time)
    const ts = new Date(Date.now() - (count - i) * 60000).toISOString();

    // Simulate realistic P&L movement
    const pnlChange = (Math.random() - 0.5) * 100; // -$50 to +$50 per snapshot
    cumulativePnL += pnlChange;

    // Calculate current equity
    const totalValue = startingBalance + cumulativePnL;

    // Calculate drawdown (negative value)
    const highWaterMark = startingBalance + Math.max(0, cumulativePnL);
    const drawdown = Math.min(0, totalValue - highWaterMark);

    snapshots.push({
      ts,
      total_value: totalValue,
      unrealized_pnl: cumulativePnL,
      realized_pnl: 0,
      cash_balance: startingBalance,
      margin_used: Math.abs(cumulativePnL * 0.1), // Simplified margin calculation
      buying_power: startingBalance * 4, // 4x leverage (Apex rules)
    });
  }

  return snapshots;
}

export const dashboardHandlers = [
  /**
   * Portfolio Snapshots
   * GET /api/v1/portfolio/snapshots
   *
   * Returns historical portfolio snapshots for equity curve chart
   */
  http.get('/api/v1/portfolio/snapshots', () => {
    return HttpResponse.json({
      snapshots: generatePortfolioSnapshots(50),
    });
  }),

  /**
   * Current Portfolio Status
   * GET /api/v1/portfolio/current
   *
   * Returns current portfolio state
   */
  http.get('/api/v1/portfolio/current', () => {
    const snapshots = generatePortfolioSnapshots(1);
    return HttpResponse.json(snapshots[0]);
  }),

  /**
   * Open Positions
   * GET /api/v1/positions
   *
   * Returns currently open trading positions
   */
  http.get('/api/v1/positions', () => {
    return HttpResponse.json({
      positions: [
        {
          symbol: 'NQ',
          side: 'LONG',
          contracts: 2,
          entry_price: 16450.25,
          current_price: 16475.50,
          unrealized_pnl: 202.00, // (16475.50 - 16450.25) * 2 * $20 (NQ point value)
          ticks: 101, // (16475.50 - 16450.25) / 0.25
        },
      ],
    });
  }),

  /**
   * Risk Status
   * GET /api/v1/risk/status
   *
   * Returns current risk metrics
   */
  http.get('/api/v1/risk/status', () => {
    return HttpResponse.json({
      current_pnl: -450.00,
      account_balance: 25000,
      max_daily_loss: 1000,
      trailing_threshold: 2000,
      risk_level: 'MODERATE',
    });
  }),

  /**
   * Recent Orders
   * GET /api/v1/orders/recent
   *
   * Returns last 10 orders
   */
  http.get('/api/v1/orders/recent', () => {
    return HttpResponse.json({
      orders: [
        {
          client_order_id: 'ORD-12345678',
          side: 'BUY',
          contracts: 2,
          status: 'FILLED',
          fill_price: 16450.25,
          timestamp: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
        },
        {
          client_order_id: 'ORD-12345679',
          side: 'SELL',
          contracts: 1,
          status: 'FILLED',
          fill_price: 16475.50,
          timestamp: new Date(Date.now() - 120000).toISOString(), // 2 minutes ago
        },
      ],
    });
  }),
];
