/**
 * Auth API Mock Handlers
 */

import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

export const authHandlers = [
  // Login
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = await request.json() as any;

    if (body.email === 'test@nqhub.com' && body.password === 'password123') {
      return HttpResponse.json({
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: {
          id: '1',
          email: 'test@nqhub.com',
          full_name: 'Test User',
          role: 'trader',
          is_active: true,
          is_verified: true,
        }
      });
    }

    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  // Get current user
  http.get(`${API_BASE}/auth/me`, () => {
    const token = localStorage.getItem('nqhub_access_token');

    if (token) {
      return HttpResponse.json({
        id: '1',
        email: 'test@nqhub.com',
        full_name: 'Test User',
        role: 'trader',
        is_active: true,
        is_verified: true,
        created_at: '2024-01-01T00:00:00Z',
      });
    }

    return HttpResponse.json(
      { detail: 'Not authenticated' },
      { status: 401 }
    );
  }),

  // Logout
  http.post(`${API_BASE}/auth/logout`, () => {
    return HttpResponse.json({ message: 'Logged out successfully' });
  }),

  // Register
  http.post(`${API_BASE}/auth/register`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json({
      id: '2',
      email: body.email,
      full_name: body.full_name,
      role: 'trader',
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
    });
  }),
];