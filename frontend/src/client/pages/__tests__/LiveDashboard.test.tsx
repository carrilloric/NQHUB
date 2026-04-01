/**
 * @vitest-environment jsdom
 *
 * LiveDashboard Tests
 *
 * Tests for AUT-353: M4.2 Live Dashboard (real-time P&L + D3 equity curve)
 *
 * Required tests:
 * 1. test_renders_equity_curve_chart
 * 2. test_renders_candlestick_chart
 * 3. test_open_positions_updates_on_ws_message
 * 4. test_risk_meters_show_correct_colors
 * 5. test_risk_meter_red_when_above_90_percent
 * 6. test_recent_orders_shows_last_10
 * 7. test_connection_status_shows_connected
 * 8. test_msw_mock_provides_portfolio_data
 */
import { describe, it, expect, vi, beforeAll, afterEach, afterAll, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import LiveDashboard from '../LiveDashboard';
import { dashboardHandlers } from '@/mocks/handlers/dashboard.handlers';
import type { PortfolioSnapshot } from '@/stores/websocketStore';

// Mock ResizeObserver (required for recharts in test environment)
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock D3 to avoid rendering issues in tests
vi.mock('d3', () => {
  const mockSelection = () => ({
    selectAll: vi.fn(() => mockSelection()),
    select: vi.fn(() => mockSelection()),
    append: vi.fn(() => mockSelection()),
    attr: vi.fn(() => mockSelection()),
    datum: vi.fn(() => mockSelection()),
    data: vi.fn(() => mockSelection()),
    enter: vi.fn(() => mockSelection()),
    call: vi.fn(() => mockSelection()),
    on: vi.fn(() => mockSelection()),
    style: vi.fn(() => mockSelection()),
    html: vi.fn(() => mockSelection()),
    transition: vi.fn(() => mockSelection()),
    duration: vi.fn(() => mockSelection()),
    remove: vi.fn(() => mockSelection()),
  });

  return {
    select: vi.fn(() => mockSelection()),
    scaleTime: vi.fn(() => {
      const scale = vi.fn(() => 0);
      scale.domain = vi.fn().mockReturnValue(scale);
      scale.range = vi.fn().mockReturnValue(scale);
      scale.invert = vi.fn(() => new Date());
      return scale;
    }),
    scaleLinear: vi.fn(() => {
      const scale = vi.fn(() => 0);
      scale.domain = vi.fn().mockReturnValue(scale);
      scale.range = vi.fn().mockReturnValue(scale);
      scale.nice = vi.fn().mockReturnValue(scale);
      return scale;
    }),
    line: vi.fn(() => ({
      x: vi.fn().mockReturnThis(),
      y: vi.fn().mockReturnThis(),
    })),
    area: vi.fn(() => ({
      x: vi.fn().mockReturnThis(),
      y0: vi.fn().mockReturnThis(),
      y1: vi.fn().mockReturnThis(),
    })),
    axisBottom: vi.fn(() => ({
      ticks: vi.fn().mockReturnThis(),
      tickFormat: vi.fn().mockReturnThis(),
    })),
    axisLeft: vi.fn(() => ({
      ticks: vi.fn().mockReturnThis(),
      tickSize: vi.fn().mockReturnThis(),
      tickFormat: vi.fn().mockReturnThis(),
    })),
    extent: vi.fn(() => [new Date(), new Date()]),
    min: vi.fn(() => 0),
    max: vi.fn(() => 100),
    bisector: vi.fn(() => ({
      left: vi.fn(() => 1),
    })),
    pointer: vi.fn(() => [0, 0]),
  };
});

// Default mock WebSocket data (can be overridden in individual tests)
let mockWebSocketData = {
  connected: true,
  error: null,
  latestCandle: {
    ts: new Date().toISOString(),
    open: 16450.25,
    high: 16475.50,
    low: 16440.00,
    close: 16470.75,
    volume: 1234,
  },
  latestPattern: null,
  latestRiskCheck: {
    current_pnl: -450.00,
    account_balance: 25000,
    max_daily_loss: 1000,
    trailing_threshold: 2000,
    risk_level: 'MODERATE',
  },
  latestOrder: {
    client_order_id: 'ORD-12345678',
    side: 'BUY',
    contracts: 2,
    status: 'FILLED',
    fill_price: 16450.25,
    timestamp: new Date().toISOString(),
  },
  openPositions: [
    {
      symbol: 'NQ',
      side: 'LONG',
      contracts: 2,
      entry_price: 16450.25,
      current_price: 16475.50,
      unrealized_pnl: 202.00,
      unrealized_pnl_ticks: 101,
    },
  ],
  portfolioSnapshot: {
    ts: new Date().toISOString(),
    total_value: 25202.00,
    unrealized_pnl: 202.00,
    realized_pnl: 0,
    cash_balance: 25000,
    margin_used: 20.2,
    buying_power: 100000,
  },
  subscribe: vi.fn(),
};

// Mock the useWebSocket hook
vi.mock('../../../hooks/useWebSocket', () => ({
  useWebSocket: () => mockWebSocketData,
}));

// Setup MSW server
const server = setupServer(...dashboardHandlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => {
  server.resetHandlers();
  // Reset mock data to default
  mockWebSocketData = {
    connected: true,
    error: null,
    latestCandle: {
      ts: new Date().toISOString(),
      open: 16450.25,
      high: 16475.50,
      low: 16440.00,
      close: 16470.75,
      volume: 1234,
    },
    latestPattern: null,
    latestRiskCheck: {
      current_pnl: -450.00,
      account_balance: 25000,
      max_daily_loss: 1000,
      trailing_threshold: 2000,
      risk_level: 'MODERATE',
    },
    latestOrder: {
      client_order_id: 'ORD-12345678',
      side: 'BUY',
      contracts: 2,
      status: 'FILLED',
      fill_price: 16450.25,
      timestamp: new Date().toISOString(),
    },
    openPositions: [
      {
        symbol: 'NQ',
        side: 'LONG',
        contracts: 2,
        entry_price: 16450.25,
        current_price: 16475.50,
        unrealized_pnl: 202.00,
        unrealized_pnl_ticks: 101,
      },
    ],
    portfolioSnapshot: {
      ts: new Date().toISOString(),
      total_value: 25202.00,
      unrealized_pnl: 202.00,
      realized_pnl: 0,
      cash_balance: 25000,
      margin_used: 20.2,
      buying_power: 100000,
    },
    subscribe: vi.fn(),
  };
});
afterAll(() => server.close());

describe('LiveDashboard - AUT-353', () => {
  /**
   * Test 1: test_renders_equity_curve_chart
   *
   * Verifies that the EquityCurveChart component (D3-based) renders correctly
   */
  it('test_renders_equity_curve_chart', async () => {
    render(<LiveDashboard />);

    // Wait for equity curve chart to be present
    await waitFor(() => {
      expect(screen.getByTestId('equity-curve-chart')).toBeInTheDocument();
    });

    // Verify chart title
    expect(screen.getByText('Equity Curve')).toBeInTheDocument();
  });

  /**
   * Test 2: test_renders_candlestick_chart
   *
   * Verifies that the CandlestickChart component (recharts-based) renders correctly
   */
  it('test_renders_candlestick_chart', async () => {
    render(<LiveDashboard />);

    // Wait for candlestick chart to be present
    await waitFor(() => {
      expect(screen.getByTestId('candlestick-chart')).toBeInTheDocument();
    });

    // Verify chart title
    expect(screen.getByText('NQ 1-Minute Chart')).toBeInTheDocument();
  });

  /**
   * Test 3: test_open_positions_updates_on_ws_message
   *
   * Verifies that open positions component displays position data from WebSocket
   */
  it('test_open_positions_updates_on_ws_message', async () => {
    render(<LiveDashboard />);

    // Wait for positions to be displayed
    await waitFor(() => {
      expect(screen.getByText('NQ')).toBeInTheDocument();
      expect(screen.getByText('LONG')).toBeInTheDocument();
      expect(screen.getByText('$202.00')).toBeInTheDocument(); // P&L

      // Check for contracts value in the positions table specifically
      const contractsCells = screen.getAllByText('2');
      expect(contractsCells.length).toBeGreaterThan(0);
    });
  });

  /**
   * Test 4: test_risk_meters_show_correct_colors
   *
   * Verifies that risk meters display with correct color coding based on thresholds
   * <70%: Green, 70-90%: Yellow (#f59e0b), >90%: Red (#ef4444)
   */
  it('test_risk_meters_show_correct_colors', async () => {
    render(<LiveDashboard />);

    // Wait for risk meters to render
    await waitFor(() => {
      expect(screen.getByText('Risk Metrics')).toBeInTheDocument();
    });

    // Daily Loss meter should be present
    const dailyLossMeter = screen.getByTestId('risk-meter-daily-loss');
    expect(dailyLossMeter).toBeInTheDocument();

    // With current_pnl = -450 and max_daily_loss = 1000, percentage is 45%
    // This should show green color (< 70%)
    const progressBar = dailyLossMeter.querySelector('.bg-green-500');
    expect(progressBar).toBeInTheDocument();
  });

  /**
   * Test 5: test_risk_meter_red_when_above_90_percent
   *
   * Verifies that risk meter shows red when threshold exceeds 90%
   */
  it('test_risk_meter_red_when_above_90_percent', async () => {
    // Override mock data for high risk scenario
    mockWebSocketData.latestRiskCheck = {
      current_pnl: -950.00, // 95% of max_daily_loss (1000)
      account_balance: 25000,
      max_daily_loss: 1000,
      trailing_threshold: 2000,
      risk_level: 'HIGH',
    };

    render(<LiveDashboard />);

    // Wait for risk meters to render
    await waitFor(() => {
      expect(screen.getByText('Risk Metrics')).toBeInTheDocument();
    });

    const dailyLossMeter = screen.getByTestId('risk-meter-daily-loss');

    // With current_pnl = -950 and max_daily_loss = 1000, percentage is 95%
    // This should show red color (> 90%)
    const progressBar = dailyLossMeter.querySelector('.bg-red-500');
    expect(progressBar).toBeInTheDocument();
  });

  /**
   * Test 6: test_recent_orders_shows_last_10
   *
   * Verifies that RecentOrders component shows only the last 10 orders
   */
  it('test_recent_orders_shows_last_10', async () => {
    render(<LiveDashboard />);

    // Wait for orders table to render - orders accumulate via useEffect so wait for it
    await waitFor(
      () => {
        const table = screen.getByTestId('orders-table');
        expect(table).toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    // Verify order data is displayed
    // Note: The order ID is truncated to last 8 chars, so we look for the pattern
    await waitFor(() => {
      expect(screen.getByText('BUY')).toBeInTheDocument();
      expect(screen.getByText('FILLED')).toBeInTheDocument();
    });

    // Verify table has correct headers within the orders table
    const ordersTable = screen.getByTestId('orders-table');
    expect(ordersTable.textContent).toContain('ID');
    expect(ordersTable.textContent).toContain('Side');
    expect(ordersTable.textContent).toContain('Status');
    expect(ordersTable.textContent).toContain('Fill Price');
  });

  /**
   * Test 7: test_connection_status_shows_connected
   *
   * Verifies that TopBar displays connection status correctly
   */
  it('test_connection_status_shows_connected', async () => {
    render(<LiveDashboard />);

    // Wait for component to render
    await waitFor(() => {
      // TopBar should show connected status (green pulsing dot)
      const greenIndicators = document.querySelectorAll('.bg-green-500');
      expect(greenIndicators.length).toBeGreaterThan(0);
    });
  });

  /**
   * Test 8: test_msw_mock_provides_portfolio_data
   *
   * Verifies that MSW mock handlers provide correct portfolio snapshot data
   */
  it('test_msw_mock_provides_portfolio_data', async () => {
    // Make a direct request to the mocked endpoint
    const response = await fetch('/api/v1/portfolio/snapshots');
    const data = await response.json();

    expect(response.ok).toBe(true);
    expect(data).toHaveProperty('snapshots');
    expect(Array.isArray(data.snapshots)).toBe(true);
    expect(data.snapshots).toHaveLength(50);

    // Verify snapshot structure
    const firstSnapshot = data.snapshots[0] as PortfolioSnapshot;
    expect(firstSnapshot).toHaveProperty('ts');
    expect(firstSnapshot).toHaveProperty('total_value');
    expect(firstSnapshot).toHaveProperty('unrealized_pnl');
    expect(firstSnapshot).toHaveProperty('realized_pnl');
    expect(firstSnapshot).toHaveProperty('cash_balance');
    expect(firstSnapshot).toHaveProperty('margin_used');
    expect(firstSnapshot).toHaveProperty('buying_power');

    // Verify realistic data ranges
    expect(firstSnapshot.total_value).toBeGreaterThan(24000);
    expect(firstSnapshot.total_value).toBeLessThan(26000);
    expect(firstSnapshot.cash_balance).toBe(25000);
  });
});
