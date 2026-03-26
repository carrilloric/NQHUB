import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const riskHandlers = [
  http.get(`${API_BASE}/risk/status`, () => HttpResponse.json({
    account_equity: 100000,
    cash_balance: 95000,
    open_positions: 2,
    total_exposure: 5000,
    daily_pnl: 250,
    daily_loss_limit: -2000,
    max_drawdown: -0.1,
    current_drawdown: -0.02,
    risk_score: 3,
    alerts: []
  })),
  http.put(`${API_BASE}/risk/config`, () => HttpResponse.json({ status: 'updated' })),
  http.post(`${API_BASE}/risk/emergency-stop`, () => HttpResponse.json({ status: 'stopped' })),
];