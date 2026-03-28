import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const botsHandlers = [
  http.post(`${API_BASE}/bots/create`, () => HttpResponse.json({ id: 'bot-1', status: 'idle' })),
  http.get(`${API_BASE}/bots`, () => HttpResponse.json([])),
  http.post(`${API_BASE}/bots/:id/start`, () => HttpResponse.json({ status: 'running' })),
  http.post(`${API_BASE}/bots/:id/stop`, () => HttpResponse.json({ status: 'idle' })),
];