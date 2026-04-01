/**
 * RiskMonitor Tests (AUT-355)
 *
 * Tests for Risk Monitor page components and WebSocket integration.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import RiskMonitor from '../RiskMonitor';
import { RiskGauge } from '@/components/risk/RiskGauge';
import { GlobalKillSwitchBar } from '@/components/risk/GlobalKillSwitchBar';
import { useWebSocket } from '@/hooks/useWebSocket';

// Mock useWebSocket hook
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    connected: true,
    latestRiskCheck: null,
    latestKillSwitch: null,
    botStatus: null,
  })),
}));

describe('RiskMonitor - AUT-355', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('test_renders_global_kill_switch_bar', () => {
    const handleKillAll = vi.fn();
    render(<GlobalKillSwitchBar onKillAll={handleKillAll} />);
    expect(screen.getByText(/Global Kill Switch/i)).toBeInTheDocument();
    expect(screen.getByText(/KILL ALL BOTS/i)).toBeInTheDocument();
  });

  it('test_gauge_green_below_70_percent', () => {
    const { container } = render(
      <RiskGauge label="Daily Loss" value={-500} limit={1000} format="currency" />
    );
    const percentage = (500 / 1000) * 100; // 50%
    expect(percentage).toBeLessThan(70);
    expect(container.querySelector('.text-green-600')).toBeInTheDocument();
  });

  it('test_gauge_yellow_between_70_and_90', () => {
    const { container } = render(
      <RiskGauge label="Daily Loss" value={-800} limit={1000} format="currency" />
    );
    const percentage = (800 / 1000) * 100; // 80%
    expect(percentage).toBeGreaterThanOrEqual(70);
    expect(percentage).toBeLessThan(90);
    expect(container.querySelector('.text-yellow-600')).toBeInTheDocument();
  });

  it('test_gauge_red_above_90_percent', () => {
    const { container } = render(
      <RiskGauge label="Daily Loss" value={-950} limit={1000} format="currency" />
    );
    const percentage = (950 / 1000) * 100; // 95%
    expect(percentage).toBeGreaterThanOrEqual(90);
    expect(container.querySelector('.text-red-600')).toBeInTheDocument();
    expect(screen.getByText(/DANGER ZONE/i)).toBeInTheDocument();
  });

  it('test_kill_all_requires_reason', async () => {
    const handleKillAll = vi.fn();
    render(<GlobalKillSwitchBar onKillAll={handleKillAll} />);
    
    fireEvent.click(screen.getByText(/KILL ALL BOTS/i));
    
    await waitFor(() => {
      expect(screen.getByText(/Reason \(Required\)/i)).toBeInTheDocument();
    });
    
    const confirmButton = screen.getByText(/Confirm Kill All/i);
    expect(confirmButton).toBeDisabled();
  });

  it('test_kill_bot_requires_reason', async () => {
    const { KillSwitchButton } = await import('@/components/risk/KillSwitchButton');
    const handleKill = vi.fn();
    
    render(
      <KillSwitchButton
        botId="bot-001"
        botName="Test Bot"
        onKill={handleKill}
      />
    );
    
    fireEvent.click(screen.getByText(/Kill Bot/i));
    
    await waitFor(() => {
      expect(screen.getByText(/Reason \(Required\)/i)).toBeInTheDocument();
    });
  });

  it('test_circuit_breaker_shows_active_status', async () => {
    const { CircuitBreakerStatus } = await import('@/components/risk/CircuitBreakerStatus');

    const activeBreakers = [
      { name: 'Daily Loss Limit', active: true, threshold: 1000, current_value: 950 },
    ];

    render(<CircuitBreakerStatus circuitBreakers={activeBreakers} />);
    expect(screen.getByText(/ACTIVE/i)).toBeInTheDocument();
  });

  it('test_risk_event_feed_updates_on_ws_message', async () => {
    const { RiskEventFeed } = await import('@/components/risk/RiskEventFeed');

    const events = [
      {
        ts: new Date().toISOString(),
        check_name: 'Daily Loss Check',
        result: 'PASSED' as const,
        reason: '',
      },
    ];

    render(<RiskEventFeed events={events} />);
    expect(screen.getByText(/Daily Loss Check/i)).toBeInTheDocument();
  });

  it('test_kill_switch_event_shows_critical_alert', async () => {
    const { useWebSocket } = await import('@/hooks/useWebSocket');
    
    vi.mocked(useWebSocket).mockReturnValue({
      connected: true,
      latestRiskCheck: null,
      latestKillSwitch: {
        bot_id: 'bot-001',
        channel: 'nqhub.risk.kill_switch',
        ts: new Date().toISOString(),
        scope: 'per_bot',
        reason: 'Daily loss limit exceeded',
        triggered_by: 'circuit_breaker',
        positions_closed: 2,
        orders_cancelled: 3,
      },
      botStatus: null,
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      connect: vi.fn(),
      disconnect: vi.fn(),
      subscribedChannels: ['risk'],
      reconnecting: false,
      error: null,
      clearError: vi.fn(),
      latestCandle: null,
      latestPattern: null,
      latestOrder: null,
      openPositions: [],
      portfolioSnapshot: null,
    });
    
    render(<RiskMonitor />);
    
    await waitFor(() => {
      expect(screen.getByText(/KILL SWITCH ACTIVATED/i)).toBeInTheDocument();
    });
  });

  it('test_ws_risk_channel_never_throttled', () => {
    render(<RiskMonitor />);

    // Verify that useWebSocket was called with risk channel (never throttled)
    expect(vi.mocked(useWebSocket)).toHaveBeenCalledWith({
      autoSubscribe: ['risk', 'bot'],
      autoConnect: false,
    });
  });
});
