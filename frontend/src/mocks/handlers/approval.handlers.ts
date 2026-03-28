import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const approvalHandlers = [
  http.get(`${API_BASE}/approval/checklist/:id`, () => HttpResponse.json({ items: [] })),
  http.post(`${API_BASE}/approval/submit`, () => HttpResponse.json({ status: 'submitted' })),
];