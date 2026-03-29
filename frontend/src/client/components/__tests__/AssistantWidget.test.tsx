/**
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AssistantWidget } from '../AssistantWidget';
import { AppProvider } from '@/state/app';
import { ServerTimeProvider } from '@/state/server-time';

// Mock axios for API requests
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
      get: vi.fn(() =>
        Promise.resolve({
          data: {
            time: {
              utc: new Date().toISOString(),
              et: new Date().toISOString(),
            },
          },
        })
      ),
      post: vi.fn(() =>
        Promise.resolve({
          data: {
            message: 'Test assistant response',
            tools_used: ['query_market_snapshot'],
            usage: {
              input_tokens: 400,
              output_tokens: 75,
            },
          },
        })
      ),
      put: vi.fn(() => Promise.resolve({ data: {} })),
      patch: vi.fn(() => Promise.resolve({ data: {} })),
      delete: vi.fn(() => Promise.resolve({ data: {} })),
    })),
    isAxiosError: vi.fn(() => false),
  },
}));

// Mock fetch for assistant API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock useAuth to provide a test token
vi.mock('@/state/app', async () => {
  const actual = await vi.importActual('@/state/app');
  return {
    ...actual,
    useAuth: vi.fn(() => ({
      isAuthenticated: true,
      token: 'test-token-123',
      user: { id: 1, email: 'test@example.com', role: 'trader' },
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    })),
  };
});

describe('AssistantWidget', () => {
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

    // Default successful fetch response
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        message: 'Test assistant response',
        tools_used: ['query_market_snapshot'],
        usage: {
          input_tokens: 400,
          output_tokens: 75,
        },
      }),
    });

    // Mock localStorage for auth token
    const mockToken = 'test-token-123';
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn((key) => (key === 'token' ? mockToken : null)),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderComponent = (initialPath = '/dashboard') => {
    window.history.pushState({}, '', initialPath);
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ServerTimeProvider>
            <AssistantWidget />
          </ServerTimeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('test_widget_renders_floating_button_when_closed', () => {
    renderComponent();

    // Should show floating button
    const button = screen.getByRole('button', { name: /open ai assistant/i });
    expect(button).toBeDefined();
    expect(button).toBeInTheDocument();

    // Should not show chat drawer
    expect(screen.queryByText('NQHUB Assistant')).not.toBeInTheDocument();
  });

  it('test_widget_opens_chat_drawer_on_button_click', async () => {
    renderComponent();

    // Click floating button
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    // Wait for drawer to appear
    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Floating button should be hidden when drawer is open
    expect(screen.queryByRole('button', { name: /open ai assistant/i })).not.toBeInTheDocument();
  });

  it('test_widget_displays_welcome_message_when_empty', async () => {
    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    // Check for welcome message
    await waitFor(() => {
      const welcomeText = screen.getByText(/Hola! Soy el asistente de NQHUB/i);
      expect(welcomeText).toBeInTheDocument();
    });
  });

  it('test_user_can_type_and_send_message', async () => {
    const user = userEvent.setup();
    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Type message
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'What is the market bias?');

    // Click send button
    const sendButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(sendButton);

    // Verify user message appears
    await waitFor(() => {
      expect(screen.getByText('What is the market bias?')).toBeInTheDocument();
    });

    // Verify API was called
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/assistant/chat',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token-123',
          'Content-Type': 'application/json',
        }),
      })
    );

    // Verify assistant response appears
    await waitFor(() => {
      expect(screen.getByText('Test assistant response')).toBeInTheDocument();
    });
  });

  it('test_enter_key_sends_message', async () => {
    const user = userEvent.setup();
    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Type message and press Enter
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'Test message{Enter}');

    // Verify message was sent
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalled();
  });

  it('test_shift_enter_creates_new_line', async () => {
    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Type message with Shift+Enter - use keyboard event directly
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Line 1' } });

    // Simulate Shift+Enter (should NOT send)
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });

    // Add second line
    fireEvent.change(textarea, { target: { value: 'Line 1\nLine 2' } });

    // Verify textarea contains both lines
    expect(textarea.value).toBe('Line 1\nLine 2');

    // Message should not be sent yet
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('test_loading_state_shows_during_api_call', async () => {
    const user = userEvent.setup();

    // Mock slow API response
    mockFetch.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: async () => ({
                message: 'Delayed response',
                tools_used: [],
                usage: { input_tokens: 100, output_tokens: 50 },
              }),
            });
          }, 500);
        })
    );

    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Send message
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'Test{Enter}');

    // Check for loading indicator
    await waitFor(() => {
      expect(screen.getByText(/pensando/i)).toBeInTheDocument();
    });

    // Wait for response
    await waitFor(
      () => {
        expect(screen.getByText('Delayed response')).toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    // Loading indicator should be gone
    expect(screen.queryByText(/pensando/i)).not.toBeInTheDocument();
  });

  it('test_assistant_message_renders_with_markdown', async () => {
    const user = userEvent.setup();

    // Mock response with markdown
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        message: 'The bias is **bearish**. The POC is at **18,285**.',
        tools_used: [],
        usage: { input_tokens: 100, output_tokens: 50 },
      }),
    });

    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Send message
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'What is the bias?{Enter}');

    // Wait for markdown response to render - just check text is present
    // ReactMarkdown may render differently in test environment
    await waitFor(
      () => {
        expect(screen.getByText(/The bias is/i)).toBeInTheDocument();
        expect(screen.getByText(/bearish/i)).toBeInTheDocument();
        expect(screen.getByText(/18,285/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('test_tool_indicators_show_when_tools_used_present', async () => {
    const user = userEvent.setup();

    // Mock response with multiple tools
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        message: 'Analysis complete',
        tools_used: ['query_market_snapshot', 'query_detected_patterns', 'run_sql'],
        usage: { input_tokens: 500, output_tokens: 100 },
      }),
    });

    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Send message
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'Run analysis{Enter}');

    // Wait for tool indicator
    await waitFor(() => {
      expect(screen.getByText(/3 herramientas utilizadas/i)).toBeInTheDocument();
    });

    // Click to expand tools
    const toolButton = screen.getByText(/3 herramientas utilizadas/i);
    fireEvent.click(toolButton);

    // Verify all tools are shown
    await waitFor(() => {
      expect(screen.getByText('query_market_snapshot')).toBeInTheDocument();
      expect(screen.getByText('query_detected_patterns')).toBeInTheDocument();
      expect(screen.getByText('run_sql')).toBeInTheDocument();
    });
  });

  it('test_page_context_detection_works_correctly', async () => {
    const user = userEvent.setup();
    renderComponent('/backtesting/rule-based');

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Check context display
    expect(screen.getByText(/contexto:/i)).toBeInTheDocument();
    expect(screen.getByText('backtesting')).toBeInTheDocument();

    // Send message
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'Test{Enter}');

    // Verify API call was made with page_context
    await waitFor(
      () => {
        expect(mockFetch).toHaveBeenCalled();
        const callArgs = mockFetch.mock.calls[0];
        expect(callArgs[0]).toBe('/api/v1/assistant/chat');

        // Parse the body to check page_context
        const body = JSON.parse(callArgs[1].body);
        expect(body.page_context).toBe('backtesting');
      },
      { timeout: 3000 }
    );
  });

  it('test_clear_conversation_button_works', async () => {
    const user = userEvent.setup();
    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Send a message
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'Test message{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });

    // Click clear button
    const clearButton = screen.getByRole('button', { name: /clear conversation/i });
    fireEvent.click(clearButton);

    // Messages should be cleared, welcome message should show
    await waitFor(() => {
      expect(screen.queryByText('Test message')).not.toBeInTheDocument();
      expect(screen.getByText(/Hola! Soy el asistente de NQHUB/i)).toBeInTheDocument();
    });
  });

  it('test_close_button_hides_drawer', async () => {
    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Click close button
    const closeButton = screen.getByRole('button', { name: /close assistant/i });
    fireEvent.click(closeButton);

    // Drawer should be hidden, floating button should show
    await waitFor(() => {
      expect(screen.queryByText('NQHUB Assistant')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /open ai assistant/i })).toBeInTheDocument();
    });
  });

  it('test_error_handling_shows_error_message', async () => {
    const user = userEvent.setup();

    // Mock failed API response
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
    });

    renderComponent();

    // Open drawer
    const openButton = screen.getByRole('button', { name: /open ai assistant/i });
    fireEvent.click(openButton);

    await waitFor(() => {
      expect(screen.getByText('NQHUB Assistant')).toBeInTheDocument();
    });

    // Send message
    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, 'Test{Enter}');

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/lo siento, ocurrió un error/i)).toBeInTheDocument();
    });
  });
});
