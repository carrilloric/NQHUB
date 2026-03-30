/**
 * MSW Handlers for Settings endpoints - AUT-359
 */

import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

// Mock data storage
let mockApexAccounts = [
  {
    id: 'apex-1',
    account_name: 'Cuenta $50K — NQ Futures',
    account_size_usd: 50000,
    trailing_threshold_usd: 2500,
    max_daily_loss_usd: 1500,
    max_contracts: 10,
    consistency_pct: 30,
    news_blackout_minutes: 5,
    status: 'connected',
  },
];

let mockCredentials = {
  rithmic_username: 'configured',
  rithmic_password: 'configured',
  rithmic_server: 'PAPER_TRADING',
  sendgrid_api_key: 'configured',
  telegram_bot_token: 'configured',
  telegram_chat_id: '123456789',
};

let mockSchedules = {
  ny_am_session: true,
  ny_pm_session: true,
  london_session: false,
  asia_session: false,
};

let mockNotifications = {
  kill_switch_activated: { telegram: true, email: true, in_app: true },
  circuit_breaker: { telegram: true, email: true, in_app: true },
  daily_loss_warning: { telegram: false, email: false, in_app: true },
  daily_loss_critical: { telegram: true, email: false, in_app: true },
  trailing_drawdown_warning: { telegram: false, email: false, in_app: true },
  trailing_drawdown_critical: { telegram: true, email: false, in_app: true },
  trade_filled: { telegram: false, email: false, in_app: false },
  bot_heartbeat_lost: { telegram: true, email: true, in_app: true },
};

export const settingsHandlers = [
  // Apex Accounts endpoints
  http.get(`${API_BASE}/settings/apex-accounts`, () => {
    return HttpResponse.json({ accounts: mockApexAccounts });
  }),

  http.post(`${API_BASE}/settings/apex-accounts`, async ({ request }) => {
    const body = (await request.json()) as any;
    const newAccount = {
      id: `apex-${Date.now()}`,
      ...body,
      status: 'disconnected',
    };
    mockApexAccounts.push(newAccount);
    return HttpResponse.json(newAccount, { status: 201 });
  }),

  http.put(`${API_BASE}/settings/apex-accounts/:id`, async ({ request, params }) => {
    const body = (await request.json()) as any;
    const accountId = params.id as string;
    const accountIndex = mockApexAccounts.findIndex((a) => a.id === accountId);

    if (accountIndex !== -1) {
      mockApexAccounts[accountIndex] = {
        ...mockApexAccounts[accountIndex],
        ...body,
      };
      return HttpResponse.json(mockApexAccounts[accountIndex]);
    }

    return HttpResponse.json({ error: 'Account not found' }, { status: 404 });
  }),

  // Test Account Connection
  http.post(`${API_BASE}/accounts/:id/test`, async ({ params }) => {
    // Simulate connection test
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const accountId = params.id as string;
    const accountIndex = mockApexAccounts.findIndex((a) => a.id === accountId);

    if (accountIndex !== -1) {
      // Randomly succeed or fail for demo
      const success = Math.random() > 0.2;
      const status = success ? 'connected' : 'disconnected';

      mockApexAccounts[accountIndex] = {
        ...mockApexAccounts[accountIndex],
        status,
      };

      return HttpResponse.json({ status });
    }

    return HttpResponse.json({ error: 'Account not found' }, { status: 404 });
  }),

  // Credentials endpoints
  http.get(`${API_BASE}/settings/credentials`, () => {
    return HttpResponse.json(mockCredentials);
  }),

  http.put(`${API_BASE}/settings/credentials/:key`, async ({ request, params }) => {
    const body = (await request.json()) as any;
    const key = params.key as string;

    // For secure fields, set status to 'configured'
    if (
      key === 'rithmic_username' ||
      key === 'rithmic_password' ||
      key === 'sendgrid_api_key' ||
      key === 'telegram_bot_token'
    ) {
      (mockCredentials as any)[key] = 'configured';
    } else {
      // For visible fields like server and chat_id, store actual value
      (mockCredentials as any)[key] = body.value;
    }

    return HttpResponse.json({ updated: true });
  }),

  // Schedules endpoints
  http.get(`${API_BASE}/settings/schedules`, () => {
    return HttpResponse.json(mockSchedules);
  }),

  http.put(`${API_BASE}/settings/schedules`, async ({ request }) => {
    const body = (await request.json()) as any;
    mockSchedules = { ...mockSchedules, ...body };
    return HttpResponse.json(mockSchedules);
  }),

  // Notifications endpoints
  http.get(`${API_BASE}/settings/notifications`, () => {
    return HttpResponse.json(mockNotifications);
  }),

  http.put(`${API_BASE}/settings/notifications`, async ({ request }) => {
    const body = (await request.json()) as any;
    mockNotifications = { ...mockNotifications, ...body };
    return HttpResponse.json(mockNotifications);
  }),

  // Test Alert endpoint
  http.post(`${API_BASE}/settings/test-alert`, async () => {
    // Simulate alert sending
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Get active channels from current config
    const activeChannels: string[] = [];
    Object.entries(mockNotifications).forEach(([event, channels]) => {
      if (channels.telegram && !activeChannels.includes('telegram')) {
        activeChannels.push('telegram');
      }
      if (channels.email && !activeChannels.includes('email')) {
        activeChannels.push('email');
      }
      if (channels.in_app && !activeChannels.includes('in_app')) {
        activeChannels.push('in_app');
      }
    });

    return HttpResponse.json({
      sent: true,
      channels: activeChannels.length > 0 ? activeChannels : ['in_app'],
    });
  }),

  // Legacy endpoint (compatibility)
  http.get(`${API_BASE}/settings/trading-schedules`, () =>
    HttpResponse.json({
      schedules: [
        {
          name: 'Regular Trading Hours',
          start_time: '09:30',
          end_time: '16:00',
          days: ['MON', 'TUE', 'WED', 'THU', 'FRI'],
        },
      ],
    })
  ),
];
