import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

// Mock order data (10 orders with various statuses)
let mockOrders = [
  {
    id: 'order-001',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    symbol: 'NQH25',
    side: 'BUY',
    quantity: 2,
    order_type: 'LIMIT',
    limit_price: 20150.50,
    stop_price: null,
    status: 'filled',
    filled_quantity: 2,
    average_fill_price: 20150.25,
    created_at: '2024-11-29T09:30:10Z',
    updated_at: '2024-11-29T09:30:15Z',
    filled_at: '2024-11-29T09:30:15Z',
  },
  {
    id: 'order-002',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    symbol: 'NQH25',
    side: 'SELL',
    quantity: 2,
    order_type: 'LIMIT',
    limit_price: 20152.75,
    stop_price: null,
    status: 'filled',
    filled_quantity: 2,
    average_fill_price: 20152.75,
    created_at: '2024-11-29T09:33:40Z',
    updated_at: '2024-11-29T09:33:42Z',
    filled_at: '2024-11-29T09:33:42Z',
  },
  {
    id: 'order-003',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    symbol: 'NQH25',
    side: 'BUY',
    quantity: 1,
    order_type: 'MARKET',
    limit_price: null,
    stop_price: null,
    status: 'filled',
    filled_quantity: 1,
    average_fill_price: 20145.75,
    created_at: '2024-11-29T11:05:10Z',
    updated_at: '2024-11-29T11:05:12Z',
    filled_at: '2024-11-29T11:05:12Z',
  },
  {
    id: 'order-004',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    symbol: 'NQH25',
    side: 'BUY',
    quantity: 2,
    order_type: 'LIMIT',
    limit_price: 20148.00,
    stop_price: null,
    status: 'pending',
    filled_quantity: 0,
    average_fill_price: null,
    created_at: '2024-11-29T13:25:30Z',
    updated_at: '2024-11-29T13:25:30Z',
    filled_at: null,
  },
  {
    id: 'order-005',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    symbol: 'NQH25',
    side: 'SELL',
    quantity: 3,
    order_type: 'STOP',
    limit_price: null,
    stop_price: 20155.00,
    status: 'pending',
    filled_quantity: 0,
    average_fill_price: null,
    created_at: '2024-11-29T13:30:00Z',
    updated_at: '2024-11-29T13:30:00Z',
    filled_at: null,
  },
  {
    id: 'order-006',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    symbol: 'NQH25',
    side: 'SELL',
    quantity: 2,
    order_type: 'LIMIT',
    limit_price: 20160.00,
    stop_price: null,
    status: 'cancelled',
    filled_quantity: 0,
    average_fill_price: null,
    created_at: '2024-11-29T12:00:00Z',
    updated_at: '2024-11-29T12:05:30Z',
    filled_at: null,
  },
  {
    id: 'order-007',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    symbol: 'NQH25',
    side: 'BUY',
    quantity: 1,
    order_type: 'MARKET',
    limit_price: null,
    stop_price: null,
    status: 'rejected',
    filled_quantity: 0,
    average_fill_price: null,
    created_at: '2024-11-29T11:45:00Z',
    updated_at: '2024-11-29T11:45:01Z',
    filled_at: null,
  },
  {
    id: 'order-008',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    symbol: 'NQH25',
    side: 'BUY',
    quantity: 2,
    order_type: 'LIMIT',
    limit_price: 20155.50,
    stop_price: null,
    status: 'filled',
    filled_quantity: 2,
    average_fill_price: 20155.50,
    created_at: '2024-11-29T10:15:28Z',
    updated_at: '2024-11-29T10:15:30Z',
    filled_at: '2024-11-29T10:15:30Z',
  },
  {
    id: 'order-009',
    bot_id: '550e8400-e29b-41d4-a716-446655440001',
    bot_name: 'Scalping Bot 2',
    symbol: 'NQH25',
    side: 'SELL',
    quantity: 2,
    order_type: 'LIMIT',
    limit_price: 20151.25,
    stop_price: null,
    status: 'filled',
    filled_quantity: 2,
    average_fill_price: 20151.25,
    created_at: '2024-11-29T10:20:13Z',
    updated_at: '2024-11-29T10:20:15Z',
    filled_at: '2024-11-29T10:20:15Z',
  },
  {
    id: 'order-010',
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
    bot_name: 'Scalping Bot 1',
    symbol: 'NQH25',
    side: 'BUY',
    quantity: 1,
    order_type: 'MARKET',
    limit_price: null,
    stop_price: null,
    status: 'filled',
    filled_quantity: 1,
    average_fill_price: 20142.00,
    created_at: '2024-11-29T13:15:18Z',
    updated_at: '2024-11-29T13:15:20Z',
    filled_at: '2024-11-29T13:15:20Z',
  },
];

export const ordersHandlers = [
  // GET /api/v1/orders - with filters and pagination
  http.get(`${API_BASE}/orders`, ({ request }) => {
    const url = new URL(request.url);
    const botIdFilter = url.searchParams.get('bot_id');
    const statusFilter = url.searchParams.get('status');
    const limit = parseInt(url.searchParams.get('limit') || '50');
    const offset = parseInt(url.searchParams.get('offset') || '0');

    let filteredOrders = [...mockOrders];

    if (botIdFilter) {
      filteredOrders = filteredOrders.filter(o => o.bot_id === botIdFilter);
    }

    if (statusFilter) {
      filteredOrders = filteredOrders.filter(o => o.status === statusFilter);
    }

    const total = filteredOrders.length;
    const paginatedOrders = filteredOrders.slice(offset, offset + limit);

    return HttpResponse.json({
      orders: paginatedOrders,
      total,
      offset,
      limit,
    });
  }),

  // GET /api/v1/orders/pending - convenience endpoint
  http.get(`${API_BASE}/orders/pending`, () => {
    const pendingOrders = mockOrders.filter(o => o.status === 'pending');
    return HttpResponse.json({ orders: pendingOrders });
  }),

  // GET /api/v1/orders/:id
  http.get(`${API_BASE}/orders/:id`, ({ params }) => {
    const order = mockOrders.find(o => o.id === params.id);
    if (!order) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(order);
  }),

  // DELETE /api/v1/orders/:id - cancel order
  http.delete(`${API_BASE}/orders/:id`, ({ params }) => {
    const orderIndex = mockOrders.findIndex(o => o.id === params.id);
    if (orderIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const order = mockOrders[orderIndex];
    if (order.status !== 'pending') {
      return new HttpResponse(
        JSON.stringify({ error: 'Only pending orders can be cancelled' }),
        { status: 400 }
      );
    }

    // Update order status to cancelled
    mockOrders[orderIndex] = {
      ...order,
      status: 'cancelled',
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(mockOrders[orderIndex]);
  }),

  // POST /api/v1/orders/submit - legacy support
  http.post(`${API_BASE}/orders/submit`, () => {
    return HttpResponse.json({
      id: 'order-new',
      status: 'submitted',
      message: 'Order submitted successfully',
    });
  }),

  // POST /api/v1/orders/:id/cancel - legacy support (alternative cancel endpoint)
  http.post(`${API_BASE}/orders/:id/cancel`, ({ params }) => {
    const orderIndex = mockOrders.findIndex(o => o.id === params.id);
    if (orderIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const order = mockOrders[orderIndex];
    if (order.status !== 'pending') {
      return new HttpResponse(
        JSON.stringify({ error: 'Only pending orders can be cancelled' }),
        { status: 400 }
      );
    }

    mockOrders[orderIndex] = {
      ...order,
      status: 'cancelled',
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json({ status: 'cancelled' });
  }),
];
