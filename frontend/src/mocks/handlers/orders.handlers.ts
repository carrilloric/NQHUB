import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const ordersHandlers = [
  http.get(`${API_BASE}/orders`, () => HttpResponse.json([])),
  http.post(`${API_BASE}/orders/submit`, () => HttpResponse.json({ id: 'order-1', status: 'submitted' })),
  http.post(`${API_BASE}/orders/:id/cancel`, () => HttpResponse.json({ status: 'cancelled' })),
];