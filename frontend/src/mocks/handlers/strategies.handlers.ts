import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const strategiesHandlers = [
  http.post(`${API_BASE}/strategies/validate`, () => HttpResponse.json({ valid: true, issues: [] })),
  http.post(`${API_BASE}/strategies/save`, () => HttpResponse.json({ id: 'strategy-1', status: 'saved' })),
  http.get(`${API_BASE}/strategies`, () => HttpResponse.json([])),
];