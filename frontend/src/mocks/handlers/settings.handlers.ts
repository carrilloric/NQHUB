import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const settingsHandlers = [
  http.get(`${API_BASE}/settings/trading-schedules`, () => HttpResponse.json({
    schedules: [
      {
        name: 'Regular Trading Hours',
        start_time: '09:30',
        end_time: '16:00',
        days: ['MON', 'TUE', 'WED', 'THU', 'FRI']
      }
    ]
  })),
  http.put(`${API_BASE}/settings/notifications`, () => HttpResponse.json({ status: 'updated' })),
];