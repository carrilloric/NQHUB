/**
 * MSW handlers for Trade Journal and Order Management
 * AUT-356
 */
import { http, HttpResponse } from 'msw';

// Mock trades data
const mockTrades = [
  {
    id: 'trade-001',
    bot_id: 'bot-apex-001',
    side: 'LONG',
    entry_price: 19250.25,
    exit_price: 19260.50,
    contracts: 2,
    gross_pnl: 410.00,
    net_pnl: 408.00,
    duration_seconds: 145,
    exit_reason: 'TP_HIT',
    ts: '2026-03-31T10:15:00Z',
    notes: 'Clean FVG entry with good confirmation',
    tags: ['fvg_entry', 'apex_limit']
  },
  {
    id: 'trade-002',
    bot_id: 'bot-apex-001',
    side: 'SHORT',
    entry_price: 19270.00,
    exit_price: 19268.75,
    contracts: 1,
    gross_pnl: 25.00,
    net_pnl: 24.20,
    duration_seconds: 320,
    exit_reason: 'SL_HIT',
    ts: '2026-03-31T11:30:00Z',
    notes: '',
    tags: []
  },
  {
    id: 'trade-003',
    bot_id: 'bot-paper-002',
    side: 'LONG',
    entry_price: 19255.50,
    exit_price: 19258.25,
    contracts: 3,
    gross_pnl: 165.00,
    net_pnl: 163.50,
    duration_seconds: 87,
    exit_reason: 'TIME',
    ts: '2026-03-31T12:45:00Z',
    notes: 'Exit due to session end',
    tags: ['session_close']
  }
];

// Mock orders
const mockPendingOrders = [
  {
    id: 'order-001',
    bot_id: 'bot-apex-001',
    order_type: 'LIMIT',
    bracket_role: 'ENTRY',
    side: 'BUY',
    contracts: 2,
    limit_price: 19245.00,
    status: 'PENDING_SUBMIT',
    submitted_at: '2026-03-31T14:00:00Z'
  },
  {
    id: 'order-002',
    bot_id: 'bot-apex-001',
    order_type: 'LIMIT',
    bracket_role: 'TP',
    side: 'SELL',
    contracts: 2,
    limit_price: 19255.00,
    status: 'SUBMITTED',
    submitted_at: '2026-03-31T14:00:01Z'
  }
];

const mockFilledOrders = [
  {
    id: 'order-003',
    bot_id: 'bot-apex-001',
    order_type: 'LIMIT',
    bracket_role: 'ENTRY',
    side: 'BUY',
    contracts: 2,
    limit_price: 19250.25,
    fill_price: 19250.25,
    status: 'FILLED',
    submitted_at: '2026-03-31T10:14:00Z',
    filled_at: '2026-03-31T10:15:00Z'
  }
];

export const journalHandlers = [
  // GET /api/v1/trades - list trades with filters
  http.get('/api/v1/trades', ({ request }) => {
    const url = new URL(request.url);
    const direction = url.searchParams.get('direction');
    const botId = url.searchParams.get('bot_id');

    let filteredTrades = [...mockTrades];

    if (direction && direction !== 'ALL') {
      filteredTrades = filteredTrades.filter(t => t.side === direction);
    }

    if (botId) {
      filteredTrades = filteredTrades.filter(t => t.bot_id === botId);
    }

    const totalPnl = filteredTrades.reduce((sum, t) => sum + t.net_pnl, 0);
    const wins = filteredTrades.filter(t => t.net_pnl > 0).length;
    const losses = filteredTrades.filter(t => t.net_pnl < 0).length;
    const winRate = filteredTrades.length > 0 ? wins / filteredTrades.length : 0;

    const grossWins = filteredTrades.filter(t => t.net_pnl > 0).reduce((sum, t) => sum + t.net_pnl, 0);
    const grossLosses = Math.abs(filteredTrades.filter(t => t.net_pnl < 0).reduce((sum, t) => sum + t.net_pnl, 0));
    const profitFactor = grossLosses > 0 ? grossWins / grossLosses : grossWins > 0 ? 999 : 0;

    return HttpResponse.json({
      trades: filteredTrades,
      summary: {
        total_pnl: totalPnl,
        win_rate: winRate,
        profit_factor: profitFactor,
        total_trades: filteredTrades.length,
        wins,
        losses
      }
    });
  }),

  // GET /api/v1/trades/:id/notes - get trade notes
  http.get('/api/v1/trades/:id/notes', ({ params }) => {
    const trade = mockTrades.find(t => t.id === params.id);
    if (!trade) {
      return HttpResponse.json({ error: 'Trade not found' }, { status: 404 });
    }
    return HttpResponse.json({
      notes: trade.notes,
      tags: trade.tags
    });
  }),

  // PUT /api/v1/trades/:id/notes - update trade notes
  http.put('/api/v1/trades/:id/notes', async ({ params, request }) => {
    const body = await request.json() as { notes: string; tags: string[] };
    const trade = mockTrades.find(t => t.id === params.id);
    if (!trade) {
      return HttpResponse.json({ error: 'Trade not found' }, { status: 404 });
    }
    trade.notes = body.notes;
    trade.tags = body.tags;
    return HttpResponse.json({ success: true });
  }),

  // GET /api/v1/orders/pending - get pending orders
  http.get('/api/v1/orders/pending', () => {
    return HttpResponse.json({
      orders: mockPendingOrders
    });
  }),

  // GET /api/v1/orders - get all orders with filters
  http.get('/api/v1/orders', ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');

    if (status === 'FILLED') {
      return HttpResponse.json({ orders: mockFilledOrders });
    }

    return HttpResponse.json({
      orders: [...mockPendingOrders, ...mockFilledOrders]
    });
  }),

  // DELETE /api/v1/orders/:id - cancel order
  http.delete('/api/v1/orders/:id', ({ params }) => {
    const orderIndex = mockPendingOrders.findIndex(o => o.id === params.id);
    if (orderIndex === -1) {
      return HttpResponse.json({ error: 'Order not found or cannot be cancelled' }, { status: 400 });
    }

    const order = mockPendingOrders[orderIndex];
    if (order.status !== 'PENDING_SUBMIT' && order.status !== 'SUBMITTED') {
      return HttpResponse.json({ error: 'Order cannot be cancelled' }, { status: 400 });
    }

    mockPendingOrders.splice(orderIndex, 1);
    return HttpResponse.json({ success: true });
  }),
];
