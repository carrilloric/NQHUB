import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const mlHandlers = [
  http.get(`${API_BASE}/ml/models`, () => HttpResponse.json([])),
  http.post(`${API_BASE}/ml/train`, () => HttpResponse.json({ id: 'model-1', status: 'training' })),
  http.post(`${API_BASE}/ml/predict`, () => HttpResponse.json({ prediction: 1, confidence: 0.85 })),
];