import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const tradesHandlers = [
  http.get(`${API_BASE}/trades`, () => HttpResponse.json([])),
  http.get(`${API_BASE}/trades/performance`, () => HttpResponse.json({
    total_trades: 100,
    winning_trades: 60,
    losing_trades: 40,
    win_rate: 0.6,
    gross_pnl: 5000,
    net_pnl: 4500,
    commissions: 500,
    average_win: 150,
    average_loss: -75,
    profit_factor: 1.5,
    max_win: 500,
    max_loss: -200,
    consecutive_wins: 5,
    consecutive_losses: 3,
    daily_stats: []
  })),
  http.get(`${API_BASE}/trades/:id`, ({ params }) => HttpResponse.json({
    id: params.id,
    order_id: 'order-1',
    symbol: 'NQ',
    side: 'buy',
    quantity: 1,
    price: 16800,
    commission: 2.5,
    executed_at: new Date().toISOString()
  })),
];