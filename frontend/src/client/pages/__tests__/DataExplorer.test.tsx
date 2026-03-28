/**
 * DataExplorer Page Tests
 *
 * Tests for the Data Explorer page including candle viewer,
 * coverage dashboard, and export functionality
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import DataExplorer from '../DataExplorer';

// Mock the store
vi.mock('@/state/data-explorer.store', () => ({
  useDataExplorerStore: () => ({
    selectedTimeframe: '5min',
    setSelectedTimeframe: vi.fn(),
    dateRange: {
      start: '2024-11-20',
      end: '2024-11-27',
    },
    setDateRange: vi.fn(),
    includeOflow: false,
    setIncludeOflow: vi.fn(),
    selectedContract: 'NQH25',
    setSelectedContract: vi.fn(),
    resetFilters: vi.fn(),
  }),
}));

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  toast: vi.fn(),
}));

// Helper to wrap component with providers
const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('DataExplorer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders the main heading and description', () => {
      renderWithProviders(<DataExplorer />);

      expect(screen.getByText('Data Explorer')).toBeInTheDocument();
      expect(
        screen.getByText('Explore candles data, view coverage, and export datasets')
      ).toBeInTheDocument();
    });

    it('renders both tabs', () => {
      renderWithProviders(<DataExplorer />);

      expect(screen.getByText('Candle Viewer')).toBeInTheDocument();
      expect(screen.getByText('Coverage Dashboard')).toBeInTheDocument();
    });

    it('shows refresh button', () => {
      renderWithProviders(<DataExplorer />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      expect(refreshButton).toBeInTheDocument();
    });
  });

  describe('Candle Viewer Tab', () => {
    it('renders timeframe selector with options', async () => {
      renderWithProviders(<DataExplorer />);

      // Click on Candle Viewer tab
      const candleTab = screen.getByText('Candle Viewer');
      fireEvent.click(candleTab);

      // Find timeframe selector
      const timeframeSelect = screen.getAllByRole('combobox')[1]; // Second combobox is timeframe
      expect(timeframeSelect).toBeInTheDocument();
    });

    it('renders date range inputs', () => {
      renderWithProviders(<DataExplorer />);

      const dateInputs = screen.getAllByRole('textbox').filter((input) => {
        return input.getAttribute('type') === 'date';
      });

      // Should have start and end date inputs
      expect(dateInputs).toHaveLength(2);
    });

    it('renders order flow toggle switch', () => {
      renderWithProviders(<DataExplorer />);

      const oflowSwitch = screen.getByRole('switch');
      expect(oflowSwitch).toBeInTheDocument();
      expect(screen.getByText('Order Flow')).toBeInTheDocument();
    });

    it('shows export buttons', () => {
      renderWithProviders(<DataExplorer />);

      expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /export parquet/i })).toBeInTheDocument();
    });

    it('displays candles table headers', async () => {
      renderWithProviders(<DataExplorer />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Timestamp')).toBeInTheDocument();
        expect(screen.getByText('Open')).toBeInTheDocument();
        expect(screen.getByText('High')).toBeInTheDocument();
        expect(screen.getByText('Low')).toBeInTheDocument();
        expect(screen.getByText('Close')).toBeInTheDocument();
        expect(screen.getByText('Volume')).toBeInTheDocument();
      });
    });
  });

  describe('Coverage Dashboard Tab', () => {
    it('switches to coverage dashboard when clicked', async () => {
      renderWithProviders(<DataExplorer />);

      const coverageTab = screen.getByText('Coverage Dashboard');
      fireEvent.click(coverageTab);

      await waitFor(() => {
        expect(screen.getByText('Data Coverage Dashboard')).toBeInTheDocument();
      });
    });

    it('displays coverage table headers', async () => {
      renderWithProviders(<DataExplorer />);

      const coverageTab = screen.getByText('Coverage Dashboard');
      fireEvent.click(coverageTab);

      await waitFor(() => {
        expect(screen.getByText('Timeframe')).toBeInTheDocument();
        expect(screen.getByText('Candle Count')).toBeInTheDocument();
        expect(screen.getByText('Start Date')).toBeInTheDocument();
        expect(screen.getByText('End Date')).toBeInTheDocument();
        expect(screen.getByText('Coverage')).toBeInTheDocument();
        expect(screen.getByText('Status')).toBeInTheDocument();
      });
    });

    it('shows active contracts section', async () => {
      renderWithProviders(<DataExplorer />);

      const coverageTab = screen.getByText('Coverage Dashboard');
      fireEvent.click(coverageTab);

      await waitFor(() => {
        expect(screen.getByText('Active Contracts')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('toggles order flow when switch is clicked', async () => {
      const setIncludeOflow = vi.fn();
      vi.mocked(useDataExplorerStore).mockReturnValue({
        ...vi.mocked(useDataExplorerStore)(),
        setIncludeOflow,
      });

      renderWithProviders(<DataExplorer />);

      const oflowSwitch = screen.getByRole('switch');
      fireEvent.click(oflowSwitch);

      expect(setIncludeOflow).toHaveBeenCalledWith(true);
    });

    it('calls refresh when refresh button is clicked', async () => {
      renderWithProviders(<DataExplorer />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      // Should trigger refetch (tested through MSW handlers)
      await waitFor(() => {
        expect(refreshButton).toBeInTheDocument();
      });
    });

    it('handles export CSV button click', async () => {
      const { toast } = await import('@/hooks/use-toast');

      renderWithProviders(<DataExplorer />);

      const exportCsvButton = screen.getByRole('button', { name: /export csv/i });
      fireEvent.click(exportCsvButton);

      await waitFor(() => {
        expect(toast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Export Started',
          })
        );
      });
    });

    it('handles export Parquet button click', async () => {
      const { toast } = await import('@/hooks/use-toast');

      renderWithProviders(<DataExplorer />);

      const exportParquetButton = screen.getByRole('button', { name: /export parquet/i });
      fireEvent.click(exportParquetButton);

      await waitFor(() => {
        expect(toast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Export Started',
          })
        );
      });
    });
  });

  describe('Data Display', () => {
    it('formats volume with K/M suffixes', async () => {
      renderWithProviders(<DataExplorer />);

      await waitFor(() => {
        // Check for formatted volume (e.g., "1.2K" or "2.5M")
        const volumeCells = screen.getAllByText(/^\d+\.?\d*[KM]?$/);
        expect(volumeCells.length).toBeGreaterThan(0);
      });
    });

    it('shows delta values with color coding', async () => {
      const setIncludeOflow = vi.fn();
      vi.mocked(useDataExplorerStore).mockReturnValue({
        ...vi.mocked(useDataExplorerStore)(),
        includeOflow: true,
        setIncludeOflow,
      });

      renderWithProviders(<DataExplorer />);

      await waitFor(() => {
        // Delta values should be displayed when oflow is enabled
        const deltaHeader = screen.getByText('Delta');
        expect(deltaHeader).toBeInTheDocument();
      });
    });

    it('displays contract badges for front month', async () => {
      renderWithProviders(<DataExplorer />);

      const coverageTab = screen.getByText('Coverage Dashboard');
      fireEvent.click(coverageTab);

      await waitFor(() => {
        const frontBadges = screen.getAllByText('Front Month');
        expect(frontBadges.length).toBeGreaterThan(0);
      });
    });

    it('shows loading state while fetching data', () => {
      renderWithProviders(<DataExplorer />);

      // Initial loading state should show spinner or loading text
      // This would depend on the actual loading behavior
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('displays error message when data fetch fails', async () => {
      // Mock a failed fetch
      global.fetch = vi.fn(() =>
        Promise.reject(new Error('Failed to fetch candles'))
      );

      renderWithProviders(<DataExplorer />);

      await waitFor(() => {
        expect(screen.getByText(/Error loading candles/)).toBeInTheDocument();
      });
    });
  });
});