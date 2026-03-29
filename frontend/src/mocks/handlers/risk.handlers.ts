/**
 * MSW handlers for Risk Management endpoints
 * Based on contract-004-live-trading.yaml
 */

import { http, HttpResponse } from 'msw';

// Mock risk configuration
const mockRiskConfig = {
  max_daily_loss_usd: 2500.00,
  max_trailing_drawdown_usd: 2500.00,
  max_contracts: 10,
  max_orders_per_minute: 20,
  news_blackout_minutes: 15,
  apex_consistency_pct: 30,
  kill_switch_enabled: true
};

// Mock risk status
const mockRiskStatus = {
  daily_loss_usd: 1625.50,
  max_daily_loss_usd: 2500.00,
  trailing_drawdown_usd: 2050.00,
  trailing_threshold_usd: 2500.00,
  open_positions: 2,
  total_exposure: 403000.00,
  last_risk_check: new Date().toISOString(),
  bot_metrics: {
    '550e8400-e29b-41d4-a716-446655440000': {
      bot_id: '550e8400-e29b-41d4-a716-446655440000',
      bot_name: 'ICT_FVG_Bot',
      daily_loss_usd: 875.25,
      max_daily_loss_usd: 2500.00,
      trailing_drawdown_usd: 1050.00,
      trailing_threshold_usd: 2500.00,
      circuit_breaker_status: 'ACTIVE'
    },
    '660e8400-e29b-41d4-a716-446655440001': {
      bot_id: '660e8400-e29b-41d4-a716-446655440001',
      bot_name: 'MA_Cross_Bot',
      daily_loss_usd: 750.25,
      max_daily_loss_usd: 2500.00,
      trailing_drawdown_usd: 1000.00,
      trailing_threshold_usd: 2500.00,
      circuit_breaker_status: 'TRIGGERED',
      circuit_breaker_reason: 'Daily loss exceeded 80% threshold',
      circuit_breaker_timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString()
    }
  }
};

// Mock bots data
const mockBots = [
  {
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'ICT_FVG_Bot',
    status: 'running',
    mode: 'paper',
    strategy: 'FVG_SCALPER',
    created_at: '2024-11-29T08:00:00Z',
    started_at: '2024-11-29T09:00:00Z',
    positions_open: 1,
    orders_pending: 3,
    daily_pnl: -875.25
  },
  {
    id: '660e8400-e29b-41d4-a716-446655440001',
    name: 'MA_Cross_Bot',
    status: 'running',
    mode: 'paper',
    strategy: 'MA_CROSSOVER',
    created_at: '2024-11-29T08:00:00Z',
    started_at: '2024-11-29T09:30:00Z',
    positions_open: 1,
    orders_pending: 2,
    daily_pnl: -750.25
  }
];

export const riskHandlers = [
  // Get risk configuration
  http.get('/api/v1/risk/config', () => {
    return HttpResponse.json(mockRiskConfig);
  }),

  // Update risk configuration
  http.put('/api/v1/risk/config', async ({ request }) => {
    const body = await request.json();
    Object.assign(mockRiskConfig, body);
    return HttpResponse.json(mockRiskConfig);
  }),

  // Get risk status
  http.get('/api/v1/risk/status', () => {
    return HttpResponse.json(mockRiskStatus);
  }),

  // List bots
  http.get('/api/v1/bots', ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const mode = url.searchParams.get('mode');

    let filteredBots = [...mockBots];

    if (status) {
      filteredBots = filteredBots.filter(bot => bot.status === status);
    }

    if (mode) {
      filteredBots = filteredBots.filter(bot => bot.mode === mode);
    }

    return HttpResponse.json({
      bots: filteredBots,
      total: filteredBots.length
    });
  }),

  // Kill individual bot
  http.post('/api/v1/bots/:id/kill', async ({ params, request }) => {
    const botId = params.id;
    const body = await request.json();

    // Find and update bot status
    const bot = mockBots.find(b => b.id === botId);
    if (bot) {
      bot.status = 'killed';
    }

    return HttpResponse.json({
      bot_id: botId,
      status: 'killed',
      positions_closed: 3,
      orders_cancelled: 5,
      timestamp: new Date().toISOString(),
      reason: body.reason || 'Manual kill from Risk Monitor'
    });
  }),

  // Kill all bots (EMERGENCY STOP)
  http.post('/api/v1/bots/kill-all', async ({ request }) => {
    const body = await request.json();

    // Check safety confirmation
    if (body.confirm !== 'KILL_ALL_BOTS') {
      return new HttpResponse(
        JSON.stringify({ error: 'Safety confirmation failed' }),
        { status: 400 }
      );
    }

    // Kill all bots
    const killedBots = mockBots.filter(bot => bot.status === 'running');
    mockBots.forEach(bot => {
      if (bot.status === 'running') {
        bot.status = 'killed';
      }
    });

    return HttpResponse.json({
      killed_count: killedBots.length,
      positions_closed_total: 45,
      orders_cancelled_total: 78,
      timestamp: new Date().toISOString(),
      affected_bots: killedBots.map(bot => ({
        bot_id: bot.id,
        positions_closed: bot.positions_open,
        orders_cancelled: bot.orders_pending
      }))
    });
  }),
];