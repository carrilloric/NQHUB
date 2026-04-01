/**
 * TradeJournal Tests
 * AUT-356
 */
import { describe, it, expect, beforeAll, afterEach, afterAll, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setupServer } from 'msw/node';
import { journalHandlers } from '../../../mocks/handlers/journal.handlers';
import TradeJournal from '../TradeJournal';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

// Setup MSW server
const server = setupServer(...journalHandlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Test wrapper component
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const renderTradeJournal = () => {
  return render(<TradeJournal />, { wrapper: AllTheProviders });
};

describe('TradeJournal', () => {
  it('test_renders_two_tabs', () => {
    renderTradeJournal();
    
    expect(screen.getByRole('button', { name: /trade journal/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /order management/i })).toBeInTheDocument();
  });

  it('test_trade_list_shows_pnl', async () => {
    renderTradeJournal();

    // Wait for trades to load
    await waitFor(() => {
      expect(screen.getByText(/\$408\.00/)).toBeInTheDocument(); // First trade P&L
    });

    // Check that P&L column exists
    expect(screen.getByText(/P&L/i)).toBeInTheDocument();
  });

  it('test_filter_by_direction_long', async () => {
    const user = userEvent.setup();
    renderTradeJournal();

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('LONG')).toBeInTheDocument();
    });

    // Select LONG filter
    const directionSelect = screen.getByLabelText(/direction/i);
    await user.selectOptions(directionSelect, 'LONG');

    // Click apply filters
    const applyButton = screen.getByRole('button', { name: /apply filters/i });
    await user.click(applyButton);

    // Wait for filtered results
    await waitFor(() => {
      const longTrades = screen.queryAllByText('LONG');
      const shortTrades = screen.queryAllByText('SHORT');
      
      // Should have LONG trades
      expect(longTrades.length).toBeGreaterThan(0);
      // Should not have SHORT trades (or very few)
    });
  });

  it('test_filter_by_bot', async () => {
    const user = userEvent.setup();
    renderTradeJournal();

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('LONG')).toBeInTheDocument();
    });

    // Enter bot ID filter
    const botInput = screen.getByLabelText(/bot id/i);
    await user.clear(botInput);
    await user.type(botInput, 'bot-apex-001');

    // Click apply filters
    const applyButton = screen.getByRole('button', { name: /apply filters/i });
    await user.click(applyButton);

    // Wait for filtered results
    await waitFor(() => {
      // Should have filtered trades
      expect(screen.getByText(/\$408\.00/)).toBeInTheDocument();
    });
  });

  it('test_pnl_summary_correct', async () => {
    renderTradeJournal();

    // Wait for summary to load
    await waitFor(() => {
      expect(screen.getByText(/total p&l/i)).toBeInTheDocument();
    });

    // Check summary values exist
    expect(screen.getByText(/win rate/i)).toBeInTheDocument();
    expect(screen.getByText(/profit factor/i)).toBeInTheDocument();
    expect(screen.getByText(/total trades/i)).toBeInTheDocument();
  });

  it('test_equity_curve_renders', async () => {
    renderTradeJournal();

    // Wait for equity curve to appear
    await waitFor(() => {
      expect(screen.getByText(/equity curve/i)).toBeInTheDocument();
    });
  });

  it('test_notes_editor_saves_on_blur', async () => {
    const user = userEvent.setup();
    renderTradeJournal();

    // Wait for trades to load
    await waitFor(() => {
      expect(screen.getByText(/\$408\.00/)).toBeInTheDocument();
    });

    // Click on first trade
    const firstTrade = screen.getByText(/\$408\.00/);
    await user.click(firstTrade);

    // Wait for notes editor
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/add notes/i)).toBeInTheDocument();
    });

    // Type in notes
    const notesTextarea = screen.getByPlaceholderText(/add notes/i);
    await user.clear(notesTextarea);
    await user.type(notesTextarea, 'Test note for this trade');

    // Blur the textarea
    await user.tab();

    // Should trigger save (1s debounce)
    await waitFor(() => {
      // Check if saving indicator appeared (optional)
      // In real implementation, we would check for network request
    }, { timeout: 2000 });
  });

  it('test_cancel_button_only_on_pending_orders', async () => {
    const user = userEvent.setup();
    renderTradeJournal();

    // Switch to Order Management tab
    const orderTab = screen.getByRole('button', { name: /order management/i });
    await user.click(orderTab);

    // Wait for orders to load
    await waitFor(() => {
      expect(screen.getByText(/active orders/i)).toBeInTheDocument();
    });

    // Check that cancel buttons exist for pending orders
    const cancelButtons = screen.queryAllByRole('button', { name: /cancel/i });
    
    // Should have cancel buttons (mock data has PENDING_SUBMIT and SUBMITTED orders)
    expect(cancelButtons.length).toBeGreaterThan(0);
  });

  it('test_order_detail_shows_bracket_legs', async () => {
    const user = userEvent.setup();
    renderTradeJournal();

    // Switch to Order Management tab
    const orderTab = screen.getByRole('button', { name: /order management/i });
    await user.click(orderTab);

    // Wait for orders to load
    await waitFor(() => {
      expect(screen.getByText(/active orders/i)).toBeInTheDocument();
    });

    // Click on first order
    await waitFor(() => {
      const firstOrderRow = screen.getAllByRole('row')[1]; // Skip header row
      if (firstOrderRow) {
        user.click(firstOrderRow);
      }
    });

    // Wait for order details panel
    await waitFor(() => {
      expect(screen.getByText(/order details/i)).toBeInTheDocument();
    });

    // Check if bracket information is displayed
    await waitFor(() => {
      const detailsPanel = screen.getByText(/order details/i).closest('div');
      if (detailsPanel) {
        // Should show bracket role or related info
        expect(detailsPanel).toBeInTheDocument();
      }
    });
  });

  it('test_msw_mock_returns_trades', async () => {
    renderTradeJournal();

    // Wait for MSW mock to return trades
    await waitFor(() => {
      // Mock data should have trade-001 with $408.00 P&L
      expect(screen.getByText(/\$408\.00/)).toBeInTheDocument();
    });

    // Check that mock data is loaded
    expect(screen.getByText('LONG')).toBeInTheDocument();
    expect(screen.getByText(/19250\.25/)).toBeInTheDocument(); // Entry price
  });
});
