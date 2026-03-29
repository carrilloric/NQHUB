import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

// Mock trade data with realistic P&L (20 trades total)
let mockTrades = [
  {
    id: 'trade-001',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20150.50,
    exit_price: 20152.75,
    quantity: 2,
    pnl_usd: 22.50,
    pnl_ticks: 4.5, // 22.50 / 5.0
    entry_time: '2024-11-29T09:30:15Z',
    exit_time: '2024-11-29T09:33:42Z',
    duration_seconds: 207,
    commission: 4.20,
    notes: 'Clean FVG entry at NY open',
    tags: ['fvg_entry', 'ny_open', 'winner'],
  },
  {
    id: 'trade-002',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20155.00,
    exit_price: 20151.25,
    quantity: 2,
    pnl_usd: 37.50,
    pnl_ticks: 7.5,
    entry_time: '2024-11-29T10:15:30Z',
    exit_time: '2024-11-29T10:20:15Z',
    duration_seconds: 285,
    commission: 4.20,
    notes: 'Strong rejection at premium',
    tags: ['premium', 'rejection', 'winner'],
  },
  {
    id: 'trade-003',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20145.25,
    exit_price: 20143.50,
    quantity: 3,
    pnl_usd: -26.25,
    pnl_ticks: -5.25,
    entry_time: '2024-11-29T11:05:10Z',
    exit_time: '2024-11-29T11:08:45Z',
    duration_seconds: 215,
    commission: 6.30,
    notes: 'Stop out, false break',
    tags: ['stop_out', 'false_break', 'loser'],
  },
  {
    id: 'trade-004',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20160.00,
    exit_price: 20157.00,
    quantity: 2,
    pnl_usd: 30.00,
    pnl_ticks: 6.0,
    entry_time: '2024-11-29T12:30:00Z',
    exit_time: '2024-11-29T12:34:30Z',
    duration_seconds: 270,
    commission: 4.20,
    notes: '',
    tags: ['lunch_trade'],
  },
  {
    id: 'trade-005',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20142.00,
    exit_price: 20147.25,
    quantity: 1,
    pnl_usd: 26.25,
    pnl_ticks: 5.25,
    entry_time: '2024-11-29T13:15:20Z',
    exit_time: '2024-11-29T13:22:10Z',
    duration_seconds: 410,
    commission: 2.10,
    notes: 'Perfect OB bounce',
    tags: ['ob_bounce', 'winner'],
  },
  {
    id: 'trade-006',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20148.75,
    exit_price: 20151.00,
    quantity: 2,
    pnl_usd: 22.50,
    pnl_ticks: 4.5,
    entry_time: '2024-11-29T14:00:05Z',
    exit_time: '2024-11-29T14:03:15Z',
    duration_seconds: 190,
    commission: 4.20,
    notes: '',
    tags: [],
  },
  {
    id: 'trade-007',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20155.50,
    exit_price: 20152.25,
    quantity: 2,
    pnl_usd: 32.50,
    pnl_ticks: 6.5,
    entry_time: '2024-11-29T14:45:30Z',
    exit_time: '2024-11-29T14:50:00Z',
    duration_seconds: 270,
    commission: 4.20,
    notes: 'Clean entry and exit',
    tags: ['winner'],
  },
  {
    id: 'trade-008',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20150.00,
    exit_price: 20148.25,
    quantity: 3,
    pnl_usd: -26.25,
    pnl_ticks: -5.25,
    entry_time: '2024-11-29T15:10:10Z',
    exit_time: '2024-11-29T15:12:45Z',
    duration_seconds: 155,
    commission: 6.30,
    notes: 'Whipsaw, news event',
    tags: ['news', 'whipsaw', 'loser'],
  },
  {
    id: 'trade-009',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20162.00,
    exit_price: 20157.75,
    quantity: 2,
    pnl_usd: 42.50,
    pnl_ticks: 8.5,
    entry_time: '2024-11-29T15:30:00Z',
    exit_time: '2024-11-29T15:37:30Z',
    duration_seconds: 450,
    commission: 4.20,
    notes: 'Strong momentum move',
    tags: ['momentum', 'winner'],
  },
  {
    id: 'trade-010',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20156.25,
    exit_price: 20159.50,
    quantity: 1,
    pnl_usd: 16.25,
    pnl_ticks: 3.25,
    entry_time: '2024-11-28T09:45:10Z',
    exit_time: '2024-11-28T09:48:20Z',
    duration_seconds: 190,
    commission: 2.10,
    notes: '',
    tags: [],
  },
  {
    id: 'trade-011',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20165.75,
    exit_price: 20161.00,
    quantity: 2,
    pnl_usd: 47.50,
    pnl_ticks: 9.5,
    entry_time: '2024-11-28T10:15:30Z',
    exit_time: '2024-11-28T10:22:15Z',
    duration_seconds: 405,
    commission: 4.20,
    notes: 'Best trade of the day',
    tags: ['best_trade', 'winner'],
  },
  {
    id: 'trade-012',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20158.00,
    exit_price: 20155.75,
    quantity: 2,
    pnl_usd: -22.50,
    pnl_ticks: -4.5,
    entry_time: '2024-11-28T11:00:00Z',
    exit_time: '2024-11-28T11:02:30Z',
    duration_seconds: 150,
    commission: 4.20,
    notes: 'Quick stop out',
    tags: ['stop_out', 'loser'],
  },
  {
    id: 'trade-013',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20170.00,
    exit_price: 20166.25,
    quantity: 3,
    pnl_usd: 56.25,
    pnl_ticks: 11.25,
    entry_time: '2024-11-28T12:30:45Z',
    exit_time: '2024-11-28T12:38:10Z',
    duration_seconds: 445,
    commission: 6.30,
    notes: 'Large winner',
    tags: ['large_winner', 'winner'],
  },
  {
    id: 'trade-014',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20163.50,
    exit_price: 20166.00,
    quantity: 2,
    pnl_usd: 25.00,
    pnl_ticks: 5.0,
    entry_time: '2024-11-28T13:15:20Z',
    exit_time: '2024-11-28T13:19:50Z',
    duration_seconds: 270,
    commission: 4.20,
    notes: '',
    tags: ['afternoon'],
  },
  {
    id: 'trade-015',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20168.75,
    exit_price: 20165.50,
    quantity: 1,
    pnl_usd: 16.25,
    pnl_ticks: 3.25,
    entry_time: '2024-11-28T14:00:00Z',
    exit_time: '2024-11-28T14:05:15Z',
    duration_seconds: 315,
    commission: 2.10,
    notes: '',
    tags: [],
  },
  {
    id: 'trade-016',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20165.00,
    exit_price: 20162.50,
    quantity: 2,
    pnl_usd: -25.00,
    pnl_ticks: -5.0,
    entry_time: '2024-11-28T14:30:10Z',
    exit_time: '2024-11-28T14:33:00Z',
    duration_seconds: 170,
    commission: 4.20,
    notes: 'Chop zone, should have waited',
    tags: ['chop', 'loser'],
  },
  {
    id: 'trade-017',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20172.50,
    exit_price: 20168.75,
    quantity: 2,
    pnl_usd: 37.50,
    pnl_ticks: 7.5,
    entry_time: '2024-11-28T15:00:00Z',
    exit_time: '2024-11-28T15:06:30Z',
    duration_seconds: 390,
    commission: 4.20,
    notes: 'Late session winner',
    tags: ['late_session', 'winner'],
  },
  {
    id: 'trade-018',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20169.25,
    exit_price: 20172.00,
    quantity: 3,
    pnl_usd: 41.25,
    pnl_ticks: 8.25,
    entry_time: '2024-11-28T15:30:00Z',
    exit_time: '2024-11-28T15:37:45Z',
    duration_seconds: 465,
    commission: 6.30,
    notes: 'Strong close move',
    tags: ['close', 'winner'],
  },
  {
    id: 'trade-019',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    strategy_id: '456e7890-e89b-12d3-a456-426614174001',
    strategy_name: 'OB Bounce',
    symbol: 'NQH25',
    direction: 'short',
    entry_price: 20175.00,
    exit_price: 20173.25,
    quantity: 1,
    pnl_usd: 8.75,
    pnl_ticks: 1.75,
    entry_time: '2024-11-27T13:45:00Z',
    exit_time: '2024-11-27T13:47:30Z',
    duration_seconds: 150,
    commission: 2.10,
    notes: 'Small scalp',
    tags: ['scalp'],
  },
  {
    id: 'trade-020',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    strategy_id: '123e4567-e89b-12d3-a456-426614174000',
    strategy_name: 'FVG Scalper',
    symbol: 'NQH25',
    direction: 'long',
    entry_price: 20170.50,
    exit_price: 20174.25,
    quantity: 2,
    pnl_usd: 37.50,
    pnl_ticks: 7.5,
    entry_time: '2024-11-27T14:15:30Z',
    exit_time: '2024-11-27T14:23:00Z',
    duration_seconds: 450,
    commission: 4.20,
    notes: 'Nice trending move',
    tags: ['trending', 'winner'],
  },
];

export const tradesHandlers = [
  // GET /api/v1/trades - with filters
  http.get(`${API_BASE}/trades`, ({ request }) => {
    const url = new URL(request.url);
    const botIdFilter = url.searchParams.get('bot_id');
    const strategyIdFilter = url.searchParams.get('strategy_id');
    const directionFilter = url.searchParams.get('direction');
    const winnersOnly = url.searchParams.get('winners_only') === 'true';
    const losersOnly = url.searchParams.get('losers_only') === 'true';

    let filteredTrades = [...mockTrades];

    if (botIdFilter) {
      filteredTrades = filteredTrades.filter(t => t.bot_id === botIdFilter);
    }

    if (strategyIdFilter) {
      filteredTrades = filteredTrades.filter(t => t.strategy_id === strategyIdFilter);
    }

    if (directionFilter) {
      filteredTrades = filteredTrades.filter(t => t.direction === directionFilter);
    }

    if (winnersOnly) {
      filteredTrades = filteredTrades.filter(t => t.pnl_usd > 0);
    }

    if (losersOnly) {
      filteredTrades = filteredTrades.filter(t => t.pnl_usd < 0);
    }

    return HttpResponse.json({ trades: filteredTrades });
  }),

  // GET /api/v1/trades/:id
  http.get(`${API_BASE}/trades/:id`, ({ params }) => {
    const trade = mockTrades.find(t => t.id === params.id);
    if (!trade) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(trade);
  }),

  // PATCH /api/v1/trades/:id - update notes/tags
  http.patch(`${API_BASE}/trades/:id`, async ({ params, request }) => {
    const tradeIndex = mockTrades.findIndex(t => t.id === params.id);
    if (tradeIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const body = await request.json() as { notes?: string; tags?: string[] };

    if (body.notes !== undefined) {
      mockTrades[tradeIndex].notes = body.notes;
    }
    if (body.tags !== undefined) {
      mockTrades[tradeIndex].tags = body.tags;
    }

    return HttpResponse.json(mockTrades[tradeIndex]);
  }),

  // GET /api/v1/trades/performance (legacy)
  http.get(`${API_BASE}/trades/performance`, () => {
    const totalPnl = mockTrades.reduce((sum, t) => sum + t.pnl_usd, 0);
    const winners = mockTrades.filter(t => t.pnl_usd > 0);
    const losers = mockTrades.filter(t => t.pnl_usd < 0);
    const grossWins = winners.reduce((sum, t) => sum + t.pnl_usd, 0);
    const grossLosses = Math.abs(losers.reduce((sum, t) => sum + t.pnl_usd, 0));
    const profitFactor = grossLosses > 0 ? grossWins / grossLosses : 0;

    return HttpResponse.json({
      total_trades: mockTrades.length,
      winning_trades: winners.length,
      losing_trades: losers.length,
      win_rate: winners.length / mockTrades.length,
      gross_pnl: totalPnl,
      net_pnl: totalPnl - mockTrades.reduce((sum, t) => sum + t.commission, 0),
      commissions: mockTrades.reduce((sum, t) => sum + t.commission, 0),
      average_win: winners.length > 0 ? grossWins / winners.length : 0,
      average_loss: losers.length > 0 ? -grossLosses / losers.length : 0,
      profit_factor: profitFactor,
      max_win: Math.max(...winners.map(t => t.pnl_usd), 0),
      max_loss: Math.min(...losers.map(t => t.pnl_usd), 0),
      consecutive_wins: 0,
      consecutive_losses: 0,
      daily_stats: []
    });
  }),
];
