/**
 * Tests for Risk Monitor page
 *
 * Validates risk monitoring functionality including:
 * - Risk meters (daily loss, trailing drawdown)
 * - Color coding based on thresholds
 * - Kill switch confirmation modals
 * - Real-time alerts panel
 * - Circuit breaker status
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import RiskMonitor from '../RiskMonitor';
import { useAuth } from '@/state/app';
import { useNQHubWebSocket } from '@/hooks/useNQHubWebSocket';

// Mock the auth hook
vi.mock('@/state/app', () => ({
  useAuth: vi.fn(),
}));

// Mock the WebSocket hook
vi.mock('@/hooks/useNQHubWebSocket', () => ({
  useNQHubWebSocket: vi.fn(),
}));

// Mock API client
const mockApiClient = {
  get: vi.fn(),
  post: vi.fn(),
};

// Helper function to render with router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('RiskMonitor', () => {
  let mockLastMessage: any = {};
  let mockWebSocketHook: any;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    mockLastMessage = {};

    // Mock auth state with API client
    (useAuth as any).mockReturnValue({
      user: { id: '1', email: 'test@example.com' },
      apiClient: mockApiClient,
    });

    // Create a function that returns the current mockLastMessage
    mockWebSocketHook = vi.fn(() => ({
      connected: true,
      connectionStatus: 'connected',
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      lastMessage: mockLastMessage,
    }));

    // Mock WebSocket hook with the function
    (useNQHubWebSocket as any).mockImplementation(mockWebSocketHook);

    // Mock API responses to match the expected format (apiClient.get returns data directly)
    mockApiClient.get.mockImplementation((url) => {
      if (url === '/bots') {
        return Promise.resolve({
            bots: [
              {
                id: 'bot-1',
                name: 'NQ Scalper',
                status: 'running',
                mode: 'live',
                strategy: 'FVG_SCALPER',
                created_at: '2024-11-29T08:00:00Z',
                started_at: '2024-11-29T09:00:00Z',
                positions_open: 1,
                orders_pending: 3,
                daily_pnl: -450,
              },
              {
                id: 'bot-2',
                name: 'Trend Follower',
                status: 'running',
                mode: 'paper',
                strategy: 'MA_CROSSOVER',
                created_at: '2024-11-29T08:00:00Z',
                started_at: '2024-11-29T09:30:00Z',
                positions_open: 1,
                orders_pending: 2,
                daily_pnl: -750.25,
              },
            ],
            total: 2
        });
      }
      if (url === '/risk/config') {
        return Promise.resolve({
            max_daily_loss_usd: 1000,
            max_trailing_drawdown_usd: 2000,
            max_contracts: 10,
            max_orders_per_minute: 20,
            news_blackout_minutes: 30,
            apex_consistency_pct: 30,
            kill_switch_enabled: true,
        });
      }
      if (url === '/risk/status') {
        return Promise.resolve({
            daily_loss_usd: 450,
            max_daily_loss_usd: 1000,
            trailing_drawdown_usd: 800,
            trailing_threshold_usd: 2000,
            open_positions: 2,
            total_exposure: 403000.00,
            last_risk_check: new Date().toISOString(),
            bot_metrics: {
              'bot-1': {
                bot_id: 'bot-1',
                bot_name: 'NQ Scalper',
                daily_loss_usd: 450,
                max_daily_loss_usd: 1000,
                trailing_drawdown_usd: 800,
                trailing_threshold_usd: 2000,
                circuit_breaker_status: 'ACTIVE'
              },
              'bot-2': {
                bot_id: 'bot-2',
                bot_name: 'Trend Follower',
                daily_loss_usd: 750.25,
                max_daily_loss_usd: 1000,
                trailing_drawdown_usd: 1000,
                trailing_threshold_usd: 2000,
                circuit_breaker_status: 'ACTIVE'
              }
            }
        });
      }
      return Promise.reject(new Error('Not found'));
    });

    mockApiClient.post.mockResolvedValue({ status: 'success' });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Test 1: Daily loss meter renders with value
   */
  it('test_daily_loss_meter_renders', async () => {
    renderWithRouter(<RiskMonitor />);

    // Wait for data to load and render
    await waitFor(() => {
      // Check for daily loss meter text
      expect(screen.getByText(/Daily Loss/i)).toBeInTheDocument();

      // Check that progress bars are rendered (one for each risk metric)
      const progressBars = document.querySelectorAll('[role="progressbar"]');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  /**
   * Test 2: Trailing drawdown meter renders
   */
  it('test_trailing_drawdown_meter_renders', async () => {
    renderWithRouter(<RiskMonitor />);

    // Wait for data to load and render
    await waitFor(() => {
      // Check for trailing drawdown meter text
      expect(screen.getByText(/Trailing Drawdown/i)).toBeInTheDocument();

      // Check for proximity text
      expect(screen.getByText(/proximity to Apex threshold/i)).toBeInTheDocument();
    });
  });

  /**
   * Test 3: Meter shows green color when below 50%
   */
  it('test_meter_color_green_below_50', async () => {
    // Set up WebSocket message with 30% daily loss
    mockLastMessage.risk = {
      channel: 'risk',
      event: 'daily_loss_update',
      data: {
        bot_id: 'bot-1',
        daily_loss_usd: 300,
        limit_usd: 1000,
      },
      timestamp: new Date().toISOString(),
    };

    renderWithRouter(<RiskMonitor />);

    // Wait for render and check green color class
    await waitFor(() => {
      const meterValue = screen.getByText(/\$300/);
      expect(meterValue).toBeInTheDocument();

      // Check for green color class in parent elements
      const meterContainer = meterValue.closest('div');
      expect(meterContainer?.className).toContain('text-green-600');
    });

    // Also check the progress bar has green color
    const progressBars = document.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBeGreaterThan(0);
    const progressBar = progressBars[0] as HTMLElement;
    const indicator = progressBar.querySelector('div[data-state]');
    expect(indicator?.className).toContain('bg-green-600');
  });

  /**
   * Test 4: Meter shows yellow color when between 50-80%
   */
  it('test_meter_color_yellow_50_to_80', async () => {
    // Set up WebSocket message with 65% daily loss
    mockLastMessage.risk = {
      channel: 'risk',
      event: 'daily_loss_update',
      data: {
        bot_id: 'bot-1',
        daily_loss_usd: 650,
        limit_usd: 1000,
      },
      timestamp: new Date().toISOString(),
    };

    renderWithRouter(<RiskMonitor />);

    // Wait for render and check yellow color class
    await waitFor(() => {
      const meterValue = screen.getByText(/\$650/);
      expect(meterValue).toBeInTheDocument();

      // Check for yellow color class
      const meterContainer = meterValue.closest('div');
      expect(meterContainer?.className).toContain('text-yellow-600');
    });

    // Also check the progress bar has yellow color
    const progressBars = document.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBeGreaterThan(0);
    const progressBar = progressBars[0] as HTMLElement;
    const indicator = progressBar.querySelector('div[data-state]');
    expect(indicator?.className).toContain('bg-yellow-600');
  });

  /**
   * Test 5: Meter shows red color when above 80%
   */
  it('test_meter_color_red_above_80', async () => {
    // Set up WebSocket message with 85% daily loss
    mockLastMessage.risk = {
      channel: 'risk',
      event: 'daily_loss_update',
      data: {
        bot_id: 'bot-1',
        daily_loss_usd: 850,
        limit_usd: 1000,
      },
      timestamp: new Date().toISOString(),
    };

    renderWithRouter(<RiskMonitor />);

    // Wait for render and check red color class
    await waitFor(() => {
      const meterValue = screen.getByText(/\$850/);
      expect(meterValue).toBeInTheDocument();

      // Check for red color class
      const meterContainer = meterValue.closest('div');
      expect(meterContainer?.className).toContain('text-red-600');
    });

    // Also check the progress bar has red color
    const progressBars = document.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBeGreaterThan(0);
    const progressBar = progressBars[0] as HTMLElement;
    const indicator = progressBar.querySelector('div[data-state]');
    expect(indicator?.className).toContain('bg-red-600');
  });

  /**
   * Test 6: Kill bot button shows confirmation modal
   */
  it('test_kill_bot_shows_confirmation', async () => {
    renderWithRouter(<RiskMonitor />);

    // Wait for bots to load
    await waitFor(() => {
      expect(screen.getByText('NQ Scalper')).toBeInTheDocument();
    });

    // Find and click the Kill Bot button for first bot
    const killButtons = screen.getAllByText(/KILL BOT/i);
    expect(killButtons.length).toBeGreaterThan(0);
    fireEvent.click(killButtons[0]);

    // Check confirmation modal appears
    await waitFor(() => {
      expect(screen.getByText(/Confirm Kill Bot/i)).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to kill NQ Scalper/i)).toBeInTheDocument();
      expect(screen.getByText(/This will immediately stop the bot and close all open positions/i)).toBeInTheDocument();
    });

    // Check modal has Cancel and Kill Bot buttons
    const dialog = screen.getByRole('dialog');
    const cancelButton = within(dialog).getByText('Cancel');
    const confirmButton = within(dialog).getByText('Kill Bot');
    expect(cancelButton).toBeInTheDocument();
    expect(confirmButton).toBeInTheDocument();
  });

  /**
   * Test 7: Kill all button shows confirmation modal with warnings
   */
  it('test_kill_all_shows_confirmation', async () => {
    renderWithRouter(<RiskMonitor />);

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByText(/KILL SWITCHES/i)).toBeInTheDocument();
    });

    // Find and click the Kill All button
    const killAllButton = screen.getByText(/KILL ALL BOTS — EMERGENCY STOP/i);
    expect(killAllButton).toBeInTheDocument();

    // Verify it has prominent styling
    expect(killAllButton.className).toContain('bg-red-700');
    expect(killAllButton.className).toContain('animate-pulse');

    // Click the button
    fireEvent.click(killAllButton);

    // Check emergency stop modal appears
    await waitFor(() => {
      expect(screen.getByText(/EMERGENCY STOP CONFIRMATION/i)).toBeInTheDocument();
      expect(screen.getByText(/CRITICAL ACTION/i)).toBeInTheDocument();
      expect(screen.getByText(/Kill ALL running bots/i)).toBeInTheDocument();
      expect(screen.getByText(/Close ALL open positions/i)).toBeInTheDocument();
      expect(screen.getByText(/Cancel ALL pending orders/i)).toBeInTheDocument();
      expect(screen.getByText(/Halt ALL trading activity/i)).toBeInTheDocument();
    });

    // Check modal has Cancel and Confirm buttons
    const dialog = screen.getByRole('dialog');
    const cancelButton = within(dialog).getByText('Cancel');
    const confirmButton = within(dialog).getByText(/CONFIRM EMERGENCY STOP/i);
    expect(cancelButton).toBeInTheDocument();
    expect(confirmButton).toBeInTheDocument();
  });

  /**
   * Test 8: Alerts panel renders
   */
  it('test_alerts_panel_renders', async () => {
    // Set up WebSocket message to trigger an alert
    mockLastMessage.risk = {
      channel: 'risk',
      event: 'daily_loss_update',
      data: {
        bot_id: 'bot-1',
        daily_loss_usd: 850,
        limit_usd: 1000,
      },
      timestamp: new Date().toISOString(),
    };

    renderWithRouter(<RiskMonitor />);

    // Check alerts panel is rendered
    await waitFor(() => {
      expect(screen.getByText(/Real-Time Alerts/i)).toBeInTheDocument();
    });

    // Check for Clear button
    expect(screen.getByText('Clear')).toBeInTheDocument();

    // Trigger a high daily loss to generate alert
    mockLastMessage.risk = {
      channel: 'risk',
      event: 'daily_loss_update',
      data: {
        bot_id: 'bot-1',
        daily_loss_usd: 950,
        limit_usd: 1000,
      },
      timestamp: new Date().toISOString(),
    };

    // Re-render with new message
    renderWithRouter(<RiskMonitor />);

    // Check alert appears
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.length).toBeGreaterThan(0);
    });
  });

  /**
   * Test 9: Critical alerts have prominent styling
   */
  it('test_critical_alert_styled_prominently', async () => {
    // Trigger circuit breaker to generate CRITICAL alert
    mockLastMessage.risk = {
      channel: 'risk',
      event: 'circuit_breaker_triggered',
      data: {
        bot_id: 'bot-1',
        reason: 'Daily loss limit exceeded',
        timestamp: new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
    };

    renderWithRouter(<RiskMonitor />);

    // Wait for alert to appear
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.length).toBeGreaterThan(0);

      // Find the critical alert
      const criticalAlert = alerts.find(alert =>
        alert.textContent?.includes('Circuit breaker triggered')
      );

      expect(criticalAlert).toBeDefined();

      // Check it has red styling
      expect(criticalAlert?.className).toContain('border-red-600');
      expect(criticalAlert?.className).toContain('bg-red-50');
    });

    // Also check for CRITICAL text
    expect(screen.getByText(/CRITICAL/)).toBeInTheDocument();
  });

  /**
   * Test 10: Circuit breaker triggered shows badge
   */
  it('test_circuit_breaker_triggered_shows_badge', async () => {
    // Set up WebSocket message for circuit breaker triggered
    mockLastMessage.risk = {
      channel: 'risk',
      event: 'circuit_breaker_triggered',
      data: {
        bot_id: 'bot-1',
        reason: 'Trailing drawdown limit reached',
        timestamp: new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
    };

    renderWithRouter(<RiskMonitor />);

    // Wait for circuit breaker badge to appear
    await waitFor(() => {
      // Look for TRIGGERED badge
      const badges = screen.getAllByText('TRIGGERED');
      expect(badges.length).toBeGreaterThan(0);

      // Check badge has destructive/red variant
      const triggeredBadge = badges[0];
      const badgeElement = triggeredBadge.closest('[class*="badge"]');
      expect(badgeElement?.className).toContain('destructive');
    });

    // Also check for the reason text
    expect(screen.getByText(/Trailing drawdown limit reached/)).toBeInTheDocument();
  });
});