/**
 * MSW Handlers for Bot Management
 * Based on CONTRACT-004 Live Trading API
 */

import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

// Mock bot data
let mockBots = [
  {
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    status: 'running',
    mode: 'live',
    last_heartbeat: new Date(Date.now() - 30000).toISOString(), // 30 seconds ago
    apex_account_id: '789e0123-e89b-12d3-a456-426614174000',
    active_params: {
      stop_loss: 50,
      take_profit: 100,
      position_size: 2,
    },
  },
  {
    id: '660e8400-e29b-41d4-a716-446655440001',
    name: 'Trend Following Bot',
    strategy_id: '234e5678-e89b-12d3-a456-426614174001',
    status: 'stopped',
    mode: 'paper',
    last_heartbeat: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
    apex_account_id: null,
    active_params: {},
  },
];

// Mock state log data
const mockStateLogs: Record<string, any[]> = {
  '550e8400-e29b-41d4-a716-446655440000': [
    {
      from: 'stopped',
      to: 'running',
      reason: 'User initiated start',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      from: 'running',
      to: 'error',
      reason: 'Connection lost to Rithmic',
      timestamp: new Date(Date.now() - 3000000).toISOString(),
    },
    {
      from: 'error',
      to: 'running',
      reason: 'Connection restored',
      timestamp: new Date(Date.now() - 2940000).toISOString(),
    },
  ],
  '660e8400-e29b-41d4-a716-446655440001': [
    {
      from: 'running',
      to: 'stopped',
      reason: 'User initiated stop',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
    },
  ],
};

export const botsHandlers = [
  // GET /api/v1/bots - List all bots
  http.get(`${API_BASE}/bots`, ({ request }) => {
    const url = new URL(request.url);
    const statusFilter = url.searchParams.get('status');
    const modeFilter = url.searchParams.get('mode');

    let filteredBots = [...mockBots];

    if (statusFilter) {
      filteredBots = filteredBots.filter((bot) => bot.status === statusFilter);
    }

    if (modeFilter) {
      filteredBots = filteredBots.filter((bot) => bot.mode === modeFilter);
    }

    return HttpResponse.json({ bots: filteredBots });
  }),

  // POST /api/v1/bots/create - Create a new bot
  http.post(`${API_BASE}/bots/create`, async ({ request }) => {
    const body = (await request.json()) as any;

    const newBot = {
      id: `bot-${Date.now()}`,
      name: body.name,
      strategy_id: body.strategy_id,
      status: 'stopped',
      mode: body.mode,
      last_heartbeat: new Date().toISOString(),
      apex_account_id: body.apex_account_id || null,
      active_params: body.active_params || {},
    };

    mockBots.push(newBot);
    mockStateLogs[newBot.id] = [];

    return HttpResponse.json(
      {
        bot_id: newBot.id,
        status: 'stopped',
      },
      { status: 201 }
    );
  }),

  // POST /api/v1/bots/:id/start - Start a bot
  http.post(`${API_BASE}/bots/:id/start`, ({ params }) => {
    const { id } = params;
    const bot = mockBots.find((b) => b.id === id);

    if (!bot) {
      return HttpResponse.json(
        { detail: 'Bot not found' },
        { status: 404 }
      );
    }

    if (bot.status === 'running') {
      return HttpResponse.json(
        { detail: 'Bot is already running' },
        { status: 409 }
      );
    }

    if (bot.status === 'killed') {
      return HttpResponse.json(
        { detail: 'Cannot start a killed bot' },
        { status: 409 }
      );
    }

    // Update bot status
    const previousStatus = bot.status;
    bot.status = 'running';
    bot.last_heartbeat = new Date().toISOString();

    // Add state log entry
    if (!mockStateLogs[bot.id]) {
      mockStateLogs[bot.id] = [];
    }
    mockStateLogs[bot.id].push({
      from: previousStatus,
      to: 'running',
      reason: 'User initiated start',
      timestamp: new Date().toISOString(),
    });

    return HttpResponse.json({
      bot_id: bot.id,
      status: 'running',
      last_heartbeat: bot.last_heartbeat,
    });
  }),

  // POST /api/v1/bots/:id/stop - Stop a bot
  http.post(`${API_BASE}/bots/:id/stop`, ({ params }) => {
    const { id } = params;
    const bot = mockBots.find((b) => b.id === id);

    if (!bot) {
      return HttpResponse.json(
        { detail: 'Bot not found' },
        { status: 404 }
      );
    }

    // Update bot status
    const previousStatus = bot.status;
    bot.status = 'stopped';
    bot.last_heartbeat = new Date().toISOString();

    // Add state log entry
    if (!mockStateLogs[bot.id]) {
      mockStateLogs[bot.id] = [];
    }
    mockStateLogs[bot.id].push({
      from: previousStatus,
      to: 'stopped',
      reason: 'User initiated stop',
      timestamp: new Date().toISOString(),
    });

    return HttpResponse.json({
      bot_id: bot.id,
      status: 'stopped',
      last_heartbeat: bot.last_heartbeat,
    });
  }),

  // POST /api/v1/bots/:id/kill - Kill a bot (KILL SWITCH)
  http.post(`${API_BASE}/bots/:id/kill`, async ({ params, request }) => {
    const { id } = params;
    const body = (await request.json().catch(() => ({}))) as any;
    const bot = mockBots.find((b) => b.id === id);

    if (!bot) {
      return HttpResponse.json(
        { detail: 'Bot not found' },
        { status: 404 }
      );
    }

    // Update bot status
    const previousStatus = bot.status;
    bot.status = 'killed';
    bot.last_heartbeat = new Date().toISOString();

    // Add state log entry
    if (!mockStateLogs[bot.id]) {
      mockStateLogs[bot.id] = [];
    }
    mockStateLogs[bot.id].push({
      from: previousStatus,
      to: 'killed',
      reason: body.reason || 'User initiated kill',
      timestamp: new Date().toISOString(),
    });

    return HttpResponse.json({
      bot_id: bot.id,
      status: 'killed',
      positions_closed: 3,
      orders_cancelled: 5,
      timestamp: new Date().toISOString(),
    });
  }),

  // POST /api/v1/bots/kill-all - Kill all bots (GLOBAL KILL SWITCH)
  http.post(`${API_BASE}/bots/kill-all`, async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as any;

    // Validate confirmation string
    if (body.confirm !== 'KILL_ALL_BOTS') {
      return HttpResponse.json(
        { detail: 'Confirmation string required: KILL_ALL_BOTS' },
        { status: 400 }
      );
    }

    const runningBots = mockBots.filter((bot) => bot.status === 'running');
    const affected_bots: any[] = [];

    let positionsClosedTotal = 0;
    let ordersCancelledTotal = 0;

    runningBots.forEach((bot) => {
      const previousStatus = bot.status;
      bot.status = 'killed';
      bot.last_heartbeat = new Date().toISOString();

      const positionsClosed = Math.floor(Math.random() * 5) + 1;
      const ordersCancelled = Math.floor(Math.random() * 10) + 1;

      positionsClosedTotal += positionsClosed;
      ordersCancelledTotal += ordersCancelled;

      affected_bots.push({
        bot_id: bot.id,
        positions_closed: positionsClosed,
        orders_cancelled: ordersCancelled,
      });

      // Add state log entry
      if (!mockStateLogs[bot.id]) {
        mockStateLogs[bot.id] = [];
      }
      mockStateLogs[bot.id].push({
        from: previousStatus,
        to: 'killed',
        reason: body.reason || 'Global kill switch activated',
        timestamp: new Date().toISOString(),
      });
    });

    return HttpResponse.json({
      killed_count: runningBots.length,
      positions_closed_total: positionsClosedTotal,
      orders_cancelled_total: ordersCancelledTotal,
      timestamp: new Date().toISOString(),
      affected_bots,
    });
  }),

  // GET /api/v1/bots/:id/state-log - Get bot state transition log
  http.get(`${API_BASE}/bots/:id/state-log`, ({ params, request }) => {
    const { id } = params;
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '100', 10);

    const bot = mockBots.find((b) => b.id === id);

    if (!bot) {
      return HttpResponse.json(
        { detail: 'Bot not found' },
        { status: 404 }
      );
    }

    const states = mockStateLogs[id as string] || [];
    const limitedStates = states.slice(-limit).reverse(); // Most recent first

    return HttpResponse.json({ states: limitedStates });
  }),
];
