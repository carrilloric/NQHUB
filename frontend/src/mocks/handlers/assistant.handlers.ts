import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const assistantHandlers = [
  http.post(`${API_BASE}/assistant/chat`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json({
      message: {
        id: 'msg-' + Date.now(),
        role: 'assistant',
        content: `I understand you said: "${body.message}". How can I help you with trading today?`,
        timestamp: new Date().toISOString()
      },
      suggestions: ['Show me recent trades', 'Analyze current positions', 'Run a backtest']
    });
  }),

  http.get(`${API_BASE}/assistant/conversations`, () => HttpResponse.json([])),
];