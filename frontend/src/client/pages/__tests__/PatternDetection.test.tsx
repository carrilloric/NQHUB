/**
 * Pattern Detection Page Tests (AUT-341)
 *
 * Tests the Pattern Detection page with 3 tabs:
 * - Fair Value Gaps (FVG)
 * - Order Blocks (OB)
 * - Liquidity Pools (LP)
 */

import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { PatternDetection } from '../PatternDetection';
import { patternsHandlers } from '@/mocks/handlers/patterns.handlers';
import type {
  FVGPattern,
  OrderBlockPattern,
  LiquidityPoolPattern,
  PaginatedResponse,
} from '@shared/types/patterns.types';

// Setup MSW server
const server = setupServer(...patternsHandlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock router
vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: () => vi.fn(),
  useLocation: () => ({ pathname: '/pattern-detection' }),
}));

// Mock i18n
vi.mock('@/state/app', () => ({
  useI18n: () => ({
    t: (key: string) => key,
    currentLanguage: 'en',
    changeLanguage: vi.fn(),
  }),
}));

describe('PatternDetection Page (AUT-341)', () => {
  /**
   * Test 1: Renders three tabs
   * Verifies that all three pattern type tabs are rendered
   */
  it('test_renders_three_tabs', () => {
    render(<PatternDetection />);

    // Check that all three tabs are present
    expect(screen.getByRole('tab', { name: /fair value gaps/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /order blocks/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /liquidity pools/i })).toBeInTheDocument();

    // Check color indicators are present (AUT-341 spec)
    const fvgTab = screen.getByRole('tab', { name: /fair value gaps/i });
    expect(within(fvgTab).getAllByRole('generic')).toHaveLength(2); // Bullish + Bearish colors
  });

  /**
   * Test 2: FVG tab shows table
   * Verifies that the FVG tab displays a table with pattern data
   */
  it('test_fvg_tab_shows_table', async () => {
    render(<PatternDetection />);

    // FVG tab should be active by default
    await waitFor(() => {
      expect(screen.getByText(/fair value gaps \(fvg\)/i)).toBeInTheDocument();
    });

    // Wait for table to load
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByRole('columnheader', { name: /formation time/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /direction/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /significance/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /status/i })).toBeInTheDocument();
  });

  /**
   * Test 3: Order Block tab shows table
   * Verifies that the Order Block tab displays a table with pattern data
   */
  it('test_ob_tab_shows_table', async () => {
    const user = userEvent.setup();
    render(<PatternDetection />);

    // Click on Order Blocks tab
    const obTab = screen.getByRole('tab', { name: /order blocks/i });
    await user.click(obTab);

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText(/last candle before significant impulse/i)).toBeInTheDocument();
    });

    // Wait for table to load
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    // Check OB-specific headers
    expect(screen.getByRole('columnheader', { name: /type/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /quality/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /impulse/i })).toBeInTheDocument();
  });

  /**
   * Test 4: Liquidity Pool tab shows table
   * Verifies that the Liquidity Pool tab displays a table with pattern data
   */
  it('test_lp_tab_shows_table', async () => {
    const user = userEvent.setup();
    render(<PatternDetection />);

    // Click on Liquidity Pools tab
    const lpTab = screen.getByRole('tab', { name: /liquidity pools/i });
    await user.click(lpTab);

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText(/areas where stop-loss orders accumulate/i)).toBeInTheDocument();
    });

    // Wait for table to load
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    // Check LP-specific headers
    expect(screen.getByRole('columnheader', { name: /type/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /modal level/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /touches/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /strength/i })).toBeInTheDocument();
  });

  /**
   * Test 5: Filter by status active
   * Verifies that status filter works correctly
   */
  it('test_filter_by_status_active', async () => {
    const user = userEvent.setup();
    render(<PatternDetection />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    // Find and click status filter dropdown
    const statusFilter = screen.getByRole('combobox', { name: /filter by status/i });
    await user.click(statusFilter);

    // Select "Unmitigated" status
    const unmitigatedOption = screen.getByRole('option', { name: /unmitigated/i });
    await user.click(unmitigatedOption);

    // Wait for filtered results
    await waitFor(() => {
      const table = screen.getByRole('table');
      const rows = within(table).getAllByRole('row');
      // Should have at least header + filtered rows
      expect(rows.length).toBeGreaterThan(1);
    });

    // Check that "Unmitigated" badges are present
    await waitFor(() => {
      expect(screen.getAllByText(/unmitigated/i).length).toBeGreaterThan(0);
    });
  });

  /**
   * Test 6: Filter by timeframe
   * Verifies that timeframe filter works correctly
   */
  it('test_filter_by_timeframe', async () => {
    const user = userEvent.setup();
    render(<PatternDetection />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    // Find timeframe selector
    const timeframeSelect = screen.getByRole('combobox', { name: /timeframe/i });
    expect(timeframeSelect).toHaveValue('5min'); // Default value

    // Change timeframe to 15min
    await user.click(timeframeSelect);
    const option15min = screen.getByRole('option', { name: /15min/i });
    await user.click(option15min);

    // Verify timeframe changed
    await waitFor(() => {
      expect(timeframeSelect).toHaveValue('15min');
    });

    // Table should still be present (data re-fetched with new timeframe)
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  /**
   * Test 7: Chart overlay renders with FVG data
   * Verifies that the chart component renders when FVG data is loaded
   */
  it('test_chart_overlay_renders_with_fvg_data', async () => {
    render(<PatternDetection />);

    // Wait for chart container to render
    await waitFor(() => {
      // Chart should be in a card with title containing "candlestick chart"
      expect(screen.getByText(/candlestick chart with fvg overlay/i)).toBeInTheDocument();
    });

    // Chart container should be present
    const chartCard = screen.getByText(/candlestick chart with fvg overlay/i).closest('div');
    expect(chartCard).toBeInTheDocument();
  });

  /**
   * Test 8: MSW mock returns patterns
   * Verifies that MSW handlers correctly return mock pattern data
   */
  it('test_msw_mock_returns_patterns', async () => {
    // This test verifies the MSW setup is working
    const response = await fetch('/api/v1/patterns/fvgs?symbol=NQ&timeframe=5min&page=1&page_size=25');
    const data: PaginatedResponse<FVGPattern> = await response.json();

    // Check response structure
    expect(data).toHaveProperty('data');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('page');
    expect(data).toHaveProperty('page_size');
    expect(data).toHaveProperty('has_more');

    // Check data array
    expect(Array.isArray(data.data)).toBe(true);
    expect(data.data.length).toBeGreaterThan(0);

    // Check first pattern structure (AUT-341 spec: NQ symbol)
    const firstPattern = data.data[0];
    expect(firstPattern).toHaveProperty('id');
    expect(firstPattern).toHaveProperty('symbol');
    expect(firstPattern.symbol).toBe('NQ'); // AUT-341: NQ hardcoded
    expect(firstPattern).toHaveProperty('timeframe');
    expect(firstPattern).toHaveProperty('formation_time');
    expect(firstPattern).toHaveProperty('gap_high');
    expect(firstPattern).toHaveProperty('gap_low');
    expect(firstPattern).toHaveProperty('significance');
    expect(firstPattern).toHaveProperty('status');
  });

  /**
   * Test 9: Empty state when no patterns
   * Verifies that empty state is displayed when no patterns are returned
   */
  it('test_empty_state_when_no_patterns', async () => {
    // Override handler to return empty data
    server.use(
      http.get('/api/v1/patterns/fvgs', () => {
        return HttpResponse.json({
          data: [],
          total: 0,
          page: 1,
          page_size: 25,
          has_more: false,
        });
      })
    );

    render(<PatternDetection />);

    // Wait for empty state message
    await waitFor(() => {
      expect(screen.getByText(/no fvg patterns found/i)).toBeInTheDocument();
    });

    // Table should still be rendered (just empty)
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
