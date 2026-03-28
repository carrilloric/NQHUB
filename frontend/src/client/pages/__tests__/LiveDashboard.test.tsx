/**
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LiveDashboard from '../LiveDashboard';
import { AppProvider } from '@/state/app';
import { ServerTimeProvider } from '@/state/server-time';

// Mock axios for server time requests
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: {
          use: vi.fn(),
        },
        response: {
          use: vi.fn(),
        },
      },
      get: vi.fn(() => Promise.resolve({
        data: {
          time: {
            utc: new Date().toISOString(),
            et: new Date().toISOString(),
          }
        }
      })),
      post: vi.fn(() => Promise.resolve({ data: {} })),
      put: vi.fn(() => Promise.resolve({ data: {} })),
      patch: vi.fn(() => Promise.resolve({ data: {} })),
      delete: vi.fn(() => Promise.resolve({ data: {} })),
    })),
    isAxiosError: vi.fn(() => false),
  },
}));

// Mock WebSocket store
const mockWebSocketStore = {
  connected: true,
  connectionStatus: 'connected' as const,
  sessionId: 'test-session',
  serverVersion: '1.0.0',
  subscribedChannels: [],
  lastMessage: {
    price: null,
    orderflow: null,
    patterns: null,
    orders: null,
    positions: null,
    portfolio: null,
    risk: null,
    bot: null,
  },
  messageHistory: [],
  priceThrottleTimestamp: 0,
  priceThrottleCount: 0,
  subscribe: vi.fn(),
  unsubscribe: vi.fn(),
};

// Mock useNQHubWebSocket hook
vi.mock('@/hooks/useNQHubWebSocket', () => ({
  useNQHubWebSocket: () => ({
    connected: mockWebSocketStore.connected,
    subscribe: mockWebSocketStore.subscribe,
    unsubscribe: mockWebSocketStore.unsubscribe,
    lastMessage: mockWebSocketStore.lastMessage,
    connectionStatus: mockWebSocketStore.connectionStatus,
  }),
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
    return scale;
  }),
  scaleLinear: vi.fn(() => {
    const scale = vi.fn(() => 0);
    scale.domain = vi.fn().mockReturnValue(scale);
    scale.range = vi.fn().mockReturnValue(scale);
    return scale;
  }),
  line: vi.fn(() => ({
    x: vi.fn().mockReturnThis(),
    y: vi.fn().mockReturnThis(),
    curve: vi.fn().mockReturnThis(),
  })),
  area: vi.fn(() => ({
    x: vi.fn().mockReturnThis(),
    y0: vi.fn().mockReturnThis(),
    y1: vi.fn().mockReturnThis(),
    curve: vi.fn().mockReturnThis(),
  })),
  axisBottom: vi.fn(() => ({
    tickFormat: vi.fn().mockReturnThis(),
    ticks: vi.fn().mockReturnThis(),
  })),
  axisLeft: vi.fn(() => ({
    tickFormat: vi.fn().mockReturnThis(),
  })),
    extent: vi.fn(() => [new Date(), new Date()]),
    min: vi.fn(() => 0),
    max: vi.fn(() => 100),
    curveMonotoneX: vi.fn(),
    timeFormat: vi.fn(() => () => '12:34'),
  };
});

// Mock lightweight-charts
vi.mock('lightweight-charts', () => ({
  createChart: vi.fn(() => ({
    addCandlestickSeries: vi.fn(() => ({
      setData: vi.fn(),
      update: vi.fn(),
    })),
    addLineSeries: vi.fn(() => ({
      setData: vi.fn(),
    })),
    addHistogramSeries: vi.fn(() => ({
      setData: vi.fn(),
    })),
    timeScale: vi.fn(() => ({
      fitContent: vi.fn(),
    })),
    applyOptions: vi.fn(),
    remove: vi.fn(),
  })),
}));

describe('LiveDashboard', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Reset mock functions
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppProvider>
            <ServerTimeProvider>
              <LiveDashboard />
            </ServerTimeProvider>
          </AppProvider>
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('test_dashboard_renders_pnl_card', async () => {
    // Set mock portfolio data
    mockWebSocketStore.lastMessage.portfolio = {
      channel: 'portfolio',
      event: 'portfolioUpdate',
      data: {
        balance: 50000,
        equity: 51250.50,
        unrealized_pnl: 1250.50,
        realized_pnl_today: 875.25,
        daily_trades: 15,
        win_rate: 0.67,
        max_drawdown: 1500.00,
      },
      timestamp: new Date().toISOString(),
      bot_id: 'test-bot',
    };

    renderComponent();

    // Check that P&L card is visible
    await waitFor(() => {
      const pnlElements = screen.getAllByText('Profit & Loss');
      expect(pnlElements.length).toBeGreaterThan(0);
      expect(pnlElements[0]).toBeDefined();
    });

    // Check for balance and equity display
    const balanceElements = screen.getAllByText('Balance');
    expect(balanceElements.length).toBeGreaterThan(0);

    const balanceValueElements = screen.getAllByText('$50,000.00');
    expect(balanceValueElements.length).toBeGreaterThan(0);

    const equityElements = screen.getAllByText('Equity');
    expect(equityElements.length).toBeGreaterThan(0);

    const equityValueElements = screen.getAllByText('$51,250.50');
    expect(equityValueElements.length).toBeGreaterThan(0);

    // Check for P&L metrics
    const unrealizedElements = screen.getAllByText('Unrealized P&L');
    expect(unrealizedElements.length).toBeGreaterThan(0);

    const realizedElements = screen.getAllByText('Realized Today');
    expect(realizedElements.length).toBeGreaterThan(0);

    const totalPnlElements = screen.getAllByText('Total P&L');
    expect(totalPnlElements.length).toBeGreaterThan(0);

    // Check for stats
    const winRateElements = screen.getAllByText('Win Rate');
    expect(winRateElements.length).toBeGreaterThan(0);

    const percentElements = screen.getAllByText('67.0%');
    expect(percentElements.length).toBeGreaterThan(0);

    const tradesElements = screen.getAllByText('Trades');
    expect(tradesElements.length).toBeGreaterThan(0);

    const tradeCountElements = screen.getAllByText('15');
    expect(tradeCountElements.length).toBeGreaterThan(0);
  });

  it('test_dashboard_renders_positions_table', async () => {
    // Set mock positions data
    mockWebSocketStore.lastMessage.positions = {
      channel: 'positions',
      event: 'positionUpdated',
      data: {
        position_id: 'test-position-1',
        symbol: 'NQH25',
        side: 'LONG',
        quantity: 2,
        entry_price: 20150.00,
        current_price: 20152.50,
        unrealized_pnl: 125.00,
      },
      timestamp: new Date().toISOString(),
      bot_id: 'test-bot',
    };

    renderComponent();

    // Check that positions table is visible
    await waitFor(() => {
      const elements = screen.getAllByText('Open Positions');
      expect(elements.length).toBeGreaterThan(0);
      expect(elements[0]).toBeDefined();
    });

    // Check for table headers
    const symbolElements = screen.getAllByText('Symbol');
    expect(symbolElements.length).toBeGreaterThan(0);

    const directionElements = screen.getAllByText('Direction');
    expect(directionElements.length).toBeGreaterThan(0);

    const sizeElements = screen.getAllByText('Size');
    expect(sizeElements.length).toBeGreaterThan(0);

    const entryPriceElements = screen.getAllByText('Entry Price');
    expect(entryPriceElements.length).toBeGreaterThan(0);

    const currentPriceElements = screen.getAllByText('Current Price');
    expect(currentPriceElements.length).toBeGreaterThan(0);

    const unrealizedPnLElements = screen.getAllByText('Unrealized P&L');
    expect(unrealizedPnLElements.length).toBeGreaterThan(0);

    // Check for position data
    const nqhElements = screen.getAllByText('NQH25');
    expect(nqhElements.length).toBeGreaterThan(0);

    const longElements = screen.getAllByText('LONG');
    expect(longElements.length).toBeGreaterThan(0);

    const quantityElements = screen.getAllByText('2');
    expect(quantityElements.length).toBeGreaterThan(0);
  });

  it('test_empty_positions_shows_placeholder', async () => {
    // No positions data - should show empty state
    mockWebSocketStore.lastMessage.positions = null;

    renderComponent();

    // Check for empty state message
    await waitFor(() => {
      const noPositionsElements = screen.getAllByText('No open positions');
      expect(noPositionsElements.length).toBeGreaterThan(0);
      expect(noPositionsElements[0]).toBeDefined();

      const placeholderElements = screen.getAllByText('Positions will appear here when opened');
      expect(placeholderElements.length).toBeGreaterThan(0);
      expect(placeholderElements[0]).toBeDefined();
    });
  });

  it('test_ws_connection_status_displayed', async () => {
    // Set bot data for connection status
    mockWebSocketStore.lastMessage.bot = {
      channel: 'bot',
      event: 'botHeartbeat',
      data: {
        bot_name: 'NQ Scalper Bot',
        mode: 'paper',
        status: 'healthy',
        uptime_seconds: 3600,
        memory_usage_mb: 256,
        cpu_usage_pct: 20,
      },
      timestamp: new Date().toISOString(),
      bot_id: 'test-bot',
    };

    renderComponent();

    // Check that connection status is displayed
    await waitFor(() => {
      const connectedElements = screen.getAllByText('Connected');
      expect(connectedElements.length).toBeGreaterThan(0);
      expect(connectedElements[0]).toBeDefined();

      const botElements = screen.getAllByText('NQ Scalper Bot');
      expect(botElements.length).toBeGreaterThan(0);
      expect(botElements[0]).toBeDefined();

      const paperElements = screen.getAllByText('paper');
      expect(paperElements.length).toBeGreaterThan(0);
      expect(paperElements[0]).toBeDefined();
    });
  });

  it('test_equity_curve_renders', async () => {
    // Set mock portfolio data with equity curve
    mockWebSocketStore.lastMessage.portfolio = {
      channel: 'portfolio',
      event: 'portfolioUpdate',
      data: {
        balance: 50000,
        equity: 51250.50,
        unrealized_pnl: 1250.50,
        realized_pnl_today: 875.25,
        daily_trades: 15,
        win_rate: 0.67,
        max_drawdown: 1500.00,
        equity_curve: [
          { time: new Date().toISOString(), equity: 50000 },
          { time: new Date().toISOString(), equity: 50500 },
          { time: new Date().toISOString(), equity: 51250.50 },
        ],
        drawdown_series: [0, 100, 0],
      },
      timestamp: new Date().toISOString(),
      bot_id: 'test-bot',
    };

    renderComponent();

    // Check that equity curve component is rendered
    await waitFor(() => {
      const equityCurveElements = screen.getAllByText('Equity Curve');
      expect(equityCurveElements.length).toBeGreaterThan(0);
      expect(equityCurveElements[0]).toBeDefined();
    });

    // D3 should have been called to create the chart
    const d3Module = await import('d3');
    expect(vi.mocked(d3Module.select)).toHaveBeenCalled();
  });

  it('test_timeframe_selector_works', async () => {
    renderComponent();

    // Check that timeframe selector is present
    await waitFor(() => {
      const chartElements = screen.getAllByText('NQ Futures Chart');
      expect(chartElements.length).toBeGreaterThan(0);
      expect(chartElements[0]).toBeDefined();
    });

    // Find timeframe tabs - use getAllByRole since there are multiple
    const oneMinTabs = screen.getAllByRole('tab', { name: '1 Min' });
    const fiveMinTabs = screen.getAllByRole('tab', { name: '5 Min' });
    const fifteenMinTabs = screen.getAllByRole('tab', { name: '15 Min' });

    // Verify tabs exist
    expect(oneMinTabs.length).toBeGreaterThan(0);
    expect(fiveMinTabs.length).toBeGreaterThan(0);
    expect(fifteenMinTabs.length).toBeGreaterThan(0);

    // Verify first tab is defined and has expected properties
    expect(oneMinTabs[0]).toBeDefined();
    expect(fiveMinTabs[0]).toBeDefined();
    expect(fifteenMinTabs[0]).toBeDefined();

    // Check that at least one tab has active state initially
    const hasActiveTab = oneMinTabs.some(tab => tab.getAttribute('data-state') === 'active');
    expect(hasActiveTab).toBe(true);
  });

  it('test_subscribes_to_all_channels_on_mount', async () => {
    renderComponent();

    // Wait for useEffect to run
    await waitFor(() => {
      expect(mockWebSocketStore.subscribe).toHaveBeenCalledWith([
        'price',
        'orderflow',
        'patterns',
        'orders',
        'positions',
        'portfolio',
        'risk',
        'bot'
      ]);
    });
  });

  it('test_unsubscribes_on_unmount', () => {
    const { unmount } = renderComponent();

    // Clear previous calls from mount
    mockWebSocketStore.unsubscribe.mockClear();

    // Unmount the component
    unmount();

    // Check that unsubscribe was called
    expect(mockWebSocketStore.unsubscribe).toHaveBeenCalledWith([
      'price',
      'orderflow',
      'patterns',
      'orders',
      'positions',
      'portfolio',
      'risk',
      'bot'
    ]);
  });
});