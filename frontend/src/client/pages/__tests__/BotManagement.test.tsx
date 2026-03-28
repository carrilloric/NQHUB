/**
 * BotManagement Page Tests
 * Tests for bot management functionality including lifecycle controls and kill switches
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import BotManagement from '../BotManagement';

// Mock the WebSocket hook
vi.mock('@/hooks/useNQHubWebSocket', () => ({
  useNQHubWebSocket: () => ({
    connected: true,
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    lastMessage: null,
    connectionStatus: 'connected',
  }),
}));

// Mock the WebSocket store
vi.mock('@/state/websocket.store', () => ({
  useWebSocketMessages: () => ({
    lastMessage: null,
    messageCount: 0,
  }),
}));

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
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

describe('BotManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders the main heading and description', () => {
      renderWithProviders(<BotManagement />);

      expect(screen.getByText('Bot Management')).toBeInTheDocument();
      expect(
        screen.getByText('Create, manage, and monitor trading bots')
      ).toBeInTheDocument();
    });

    it('renders create bot button', () => {
      renderWithProviders(<BotManagement />);

      const createButton = screen.getByRole('button', { name: /create bot/i });
      expect(createButton).toBeInTheDocument();
    });
  });

  describe('Bot List', () => {
    it('test_bot_list_renders - lista de bots visible', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Scalping Bot 1')).toBeInTheDocument();
        expect(screen.getByText('Trend Following Bot')).toBeInTheDocument();
      });
    });

    it('displays bot status badges correctly', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Running')).toBeInTheDocument();
        expect(screen.getByText('Stopped')).toBeInTheDocument();
      });
    });

    it('displays bot mode (live/paper)', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('live')).toBeInTheDocument();
        expect(screen.getByText('paper')).toBeInTheDocument();
      });
    });
  });

  describe('Create Bot Form', () => {
    it('test_create_bot_form_renders - formulario visible con campos requeridos', async () => {
      renderWithProviders(<BotManagement />);

      const createButton = screen.getByRole('button', { name: /create bot/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText('Create New Bot')).toBeInTheDocument();
        expect(screen.getByLabelText('Bot Name')).toBeInTheDocument();
        expect(screen.getByLabelText('Strategy')).toBeInTheDocument();
        expect(screen.getByLabelText('Mode')).toBeInTheDocument();
      });
    });

    it('allows filling out the create bot form', async () => {
      const user = userEvent.setup();
      renderWithProviders(<BotManagement />);

      const createButton = screen.getByRole('button', { name: /create bot/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Bot Name');
        expect(nameInput).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText('Bot Name');
      await user.clear(nameInput);
      await user.type(nameInput, 'Test Bot');

      expect(nameInput).toHaveValue('Test Bot');
    });

    it('shows cancel button in create form', async () => {
      renderWithProviders(<BotManagement />);

      const createButton = screen.getByRole('button', { name: /create bot/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });
    });
  });

  describe('Bot Controls', () => {
    it('test_start_button_disabled_when_running - bot running → start deshabilitado', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        expect(rows.length).toBeGreaterThan(1); // Header + data rows
      });

      // Find the running bot row (Scalping Bot 1)
      const rows = screen.getAllByRole('row');
      const runningBotRow = rows.find((row) =>
        row.textContent?.includes('Scalping Bot 1')
      );

      expect(runningBotRow).toBeTruthy();

      // Get all buttons in the running bot row
      if (runningBotRow) {
        const buttons = runningBotRow.querySelectorAll('button');
        const startButton = buttons[0]; // First button is start

        expect(startButton).toBeDisabled();
      }
    });

    it('shows stop button enabled for running bot', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        const runningBotRow = rows.find((row) =>
          row.textContent?.includes('Scalping Bot 1')
        );

        if (runningBotRow) {
          const buttons = runningBotRow.querySelectorAll('button');
          const stopButton = buttons[1]; // Second button is stop

          expect(stopButton).not.toBeDisabled();
        }
      });
    });

    it('shows kill button enabled for non-killed bots', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        const botRow = rows.find((row) =>
          row.textContent?.includes('Scalping Bot 1')
        );

        if (botRow) {
          const buttons = botRow.querySelectorAll('button');
          const killButton = buttons[2]; // Third button is kill

          expect(killButton).not.toBeDisabled();
        }
      });
    });
  });

  describe('Kill Switch', () => {
    it('test_kill_button_shows_confirmation - click kill → modal de confirmación', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        expect(rows.length).toBeGreaterThan(1);
      });

      // Find kill button and click it
      const rows = screen.getAllByRole('row');
      const botRow = rows.find((row) =>
        row.textContent?.includes('Scalping Bot 1')
      );

      if (botRow) {
        const buttons = botRow.querySelectorAll('button');
        const killButton = buttons[2];
        fireEvent.click(killButton);

        await waitFor(() => {
          expect(screen.getByText('Are you absolutely sure?')).toBeInTheDocument();
          expect(
            screen.getByText(/This will immediately kill the bot/i)
          ).toBeInTheDocument();
        });
      }
    });

    it('shows cancel and confirm buttons in kill dialog', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        const botRow = rows.find((row) =>
          row.textContent?.includes('Scalping Bot 1')
        );

        if (botRow) {
          const buttons = botRow.querySelectorAll('button');
          const killButton = buttons[2];
          fireEvent.click(killButton);
        }
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /kill bot/i })).toBeInTheDocument();
      });
    });

    it('test_kill_all_shows_confirmation - click kill all → modal de confirmación', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        // Wait for running bots to load
        expect(screen.getByText('Running')).toBeInTheDocument();
      });

      const killAllButton = screen.getByRole('button', { name: /kill all/i });
      fireEvent.click(killAllButton);

      await waitFor(() => {
        expect(screen.getByText('Kill All Running Bots?')).toBeInTheDocument();
        expect(
          screen.getByText(/This will immediately kill all/i)
        ).toBeInTheDocument();
      });
    });

    it('shows kill all button only when there are running bots', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const killAllButton = screen.queryByRole('button', { name: /kill all/i });
        // Should be visible because we have 1 running bot (Scalping Bot 1)
        expect(killAllButton).toBeInTheDocument();
      });
    });
  });

  describe('State Log Timeline', () => {
    it('test_state_log_shows_on_bot_select - seleccionar bot → timeline visible', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        expect(rows.length).toBeGreaterThan(1);
      });

      // Click on a bot row to select it
      const rows = screen.getAllByRole('row');
      const botRow = rows.find((row) =>
        row.textContent?.includes('Scalping Bot 1')
      );

      if (botRow) {
        fireEvent.click(botRow);

        await waitFor(() => {
          expect(screen.getByText(/State Log Timeline/i)).toBeInTheDocument();
          expect(screen.getByText(/User initiated start/i)).toBeInTheDocument();
        });
      }
    });

    it('displays state transitions with timestamps', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        const botRow = rows.find((row) =>
          row.textContent?.includes('Scalping Bot 1')
        );

        if (botRow) {
          fireEvent.click(botRow);
        }
      });

      await waitFor(() => {
        // Check for state transitions (multiple "running" and "stopped" can exist in state log)
        const stoppedElements = screen.queryAllByText('stopped');
        const runningElements = screen.queryAllByText('running');

        expect(stoppedElements.length).toBeGreaterThan(0);
        expect(runningElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Heartbeat Indicator', () => {
    it('test_heartbeat_indicator_renders - indicador de heartbeat visible', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        // Heartbeat indicators should be visible for each bot
        const heartbeatTexts = screen.getAllByText(/ago$/);
        expect(heartbeatTexts.length).toBeGreaterThan(0);
      });
    });

    it('displays heartbeat time for each bot', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        // Should show "Xs ago" or "Xm ago" format
        const heartbeatPattern = /\d+[sm]\s+ago/;
        const elements = screen.getAllByText(heartbeatPattern);
        expect(elements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('WebSocket Integration', () => {
    it('displays WebSocket connection status', () => {
      renderWithProviders(<BotManagement />);

      // When disconnected, should show alert
      // When connected, alert should not be visible
      const disconnectedAlert = screen.queryByText(
        /WebSocket disconnected/i
      );
      // Should not be visible since mock shows connected: true
      expect(disconnectedAlert).not.toBeInTheDocument();
    });
  });

  describe('Data Display', () => {
    it('displays correct number of bots configured', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText(/2 bots configured/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('shows empty state when no bots exist', async () => {
      const { server: testServer } = await import('../../../mocks/server');
      const { http, HttpResponse } = await import('msw');

      // Override handler to return empty bots
      testServer.use(
        http.get('/api/v1/bots', () => {
          return HttpResponse.json({ bots: [] });
        })
      );

      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        expect(
          screen.getByText(/No bots created. Create your first bot/i)
        ).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('displays apex account ID when available', async () => {
      renderWithProviders(<BotManagement />);

      await waitFor(() => {
        // First wait for bots to load by checking if bot names are visible
        expect(screen.getByText('Scalping Bot 1')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Then check for apex account ID (truncated to first 8 chars)
      await waitFor(() => {
        const cells = screen.queryAllByText(/789e0123/i);
        expect(cells.length).toBeGreaterThan(0);
      }, { timeout: 2000 });
    });
  });
});
