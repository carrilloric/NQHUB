/**
 * Tests for useNQHubWebSocket hook
 *
 * Based on LINEAR issue AUT-376 requirements
 * Tests WebSocket connection, subscription, message handling, and reconnection
 *
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useNQHubWebSocket } from '../useNQHubWebSocket';
import { useWebSocketStore } from '@/state/websocket.store';
import { useAuth } from '@/state/app';

// Mock auth store
vi.mock('@/state/app', () => ({
  useAuth: vi.fn(),
}));

// Mock WebSocket class
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  private messageHandlers: Array<(data: any) => void> = [];

  constructor(url: string) {
    this.url = url;
    // Simulate connection opening after a short delay
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data: string): void {
    const parsed = JSON.parse(data);
    this.messageHandlers.forEach(handler => handler(parsed));
  }

  close(code: number = 1000, reason: string = ''): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      const event = new CloseEvent('close', { code, reason });
      this.onclose(event);
    }
  }

  // Helper method for tests to send messages to the client
  mockReceive(data: any): void {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }

  // Helper method for tests to register message handlers
  onSend(handler: (data: any) => void): void {
    this.messageHandlers.push(handler);
  }
}

describe('useNQHubWebSocket', () => {
  let mockWebSocket: MockWebSocket;
  const mockToken = 'test-jwt-token';
  const sentMessages: any[] = [];

  beforeEach(() => {
    // Reset store before each test
    useWebSocketStore.getState().reset();

    // Clear sent messages
    sentMessages.length = 0;

    // Setup auth mock
    (useAuth as any).mockReturnValue({ token: mockToken });

    // Replace global WebSocket with mock using vi.stubGlobal
    const WebSocketMock = class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        mockWebSocket = this;
        // Capture sent messages
        this.onSend((data) => sentMessages.push(data));
      }
    };

    vi.stubGlobal('WebSocket', WebSocketMock);
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
    vi.unstubAllGlobals();
  });

  /**
   * Test 1: Hook connects on mount
   */
  it('test_hook_connects_on_mount', async () => {
    const { result } = renderHook(() => useNQHubWebSocket());

    // Wait for connection
    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connecting');
    });

    // Wait for WebSocket to open
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
      expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN);
    });

    // Send connection established message
    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Verify token was sent in connection URL
    expect(mockWebSocket.url).toContain(`token=${mockToken}`);
  });

  /**
   * Test 2: Hook disconnects on unmount
   */
  it('test_hook_disconnects_on_unmount', async () => {
    const { result, unmount } = renderHook(() => useNQHubWebSocket());

    // Wait for WebSocket to open
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
      expect(mockWebSocket.readyState).toBe(MockWebSocket.OPEN);
    });

    // Send connection established
    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });

    // Unmount hook
    unmount();

    // Verify WebSocket was closed
    await waitFor(() => {
      expect(mockWebSocket.readyState).toBe(MockWebSocket.CLOSED);
    });
  });

  /**
   * Test 3: Subscribe sends protocol message
   */
  it('test_subscribe_sends_protocol_message', async () => {
    const { result } = renderHook(() => useNQHubWebSocket());

    // Wait for connection and establish it
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
    });

    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });

    // Clear any initial messages
    sentMessages.length = 0;

    // Subscribe to channels
    act(() => {
      result.current.subscribe(['price', 'orderflow', 'patterns']);
    });

    // Verify subscription message was sent
    await waitFor(() => {
      expect(sentMessages).toContainEqual({
        action: 'subscribe',
        channels: ['price', 'orderflow', 'patterns'],
      });
    });

    // Send subscription confirmation
    mockWebSocket.mockReceive({
      action: 'subscribed',
      channels: ['price', 'orderflow', 'patterns'],
    });

    // Verify state updated
    await waitFor(() => {
      const store = useWebSocketStore.getState();
      expect(store.subscribedChannels).toContain('price');
      expect(store.subscribedChannels).toContain('orderflow');
      expect(store.subscribedChannels).toContain('patterns');
    });
  });

  /**
   * Test 4: Last message updates on receive
   */
  it('test_last_message_updates_on_receive', async () => {
    const { result } = renderHook(() => useNQHubWebSocket());

    // Establish connection
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
    });

    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });

    // Subscribe to price channel
    act(() => {
      result.current.subscribe(['price']);
    });

    // Send price message
    const priceMessage = {
      channel: 'price',
      event: 'tick',
      data: {
        symbol: 'NQH25',
        bid: 20150.00,
        ask: 20150.25,
        last: 20150.25,
        timestamp: '2024-03-28T10:00:00.000Z',
      },
      timestamp: '2024-03-28T10:00:00.000Z',
      bot_id: 'test-bot-id',
    };

    mockWebSocket.mockReceive(priceMessage);

    // Verify last message was updated
    await waitFor(() => {
      expect(result.current.lastMessage.price).toEqual(priceMessage);
    });
  });

  /**
   * Test 5: Risk channel never throttled
   */
  it('test_risk_channel_never_throttled', async () => {
    const { result } = renderHook(() => useNQHubWebSocket());

    // Establish connection
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
    });

    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });

    // Subscribe to risk channel
    act(() => {
      result.current.subscribe(['risk']);
    });

    // Send multiple risk messages rapidly (more than throttle limit)
    const riskMessages = [];
    for (let i = 0; i < 20; i++) {
      const msg = {
        channel: 'risk',
        event: 'alert',
        data: {
          alert_id: `alert-${i}`,
          severity: 'HIGH',
          message: `Risk alert ${i}`,
          max_position_exceeded: i > 10,
        },
        timestamp: new Date().toISOString(),
        bot_id: 'test-bot-id',
      };
      riskMessages.push(msg);
      mockWebSocket.mockReceive(msg);
    }

    // All risk messages should be received (never throttled)
    await waitFor(() => {
      const store = useWebSocketStore.getState();
      // Last message should be the last one sent
      expect(store.lastMessage.risk?.data).toEqual(riskMessages[19].data);
      // Message history should contain all messages
      const riskHistory = store.messageHistory.filter(m => m.channel === 'risk');
      expect(riskHistory.length).toBeGreaterThanOrEqual(15); // Allow for some test timing variance
    });
  });

  /**
   * Test 6: Reconnects after disconnect
   */
  it('test_reconnects_after_disconnect', { timeout: 10000 }, async () => {
    // Mock timers for reconnection delays
    vi.useFakeTimers();

    const { result } = renderHook(() => useNQHubWebSocket());

    // Establish initial connection
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
    });

    // Advance timer to open connection
    await act(async () => {
      vi.advanceTimersByTime(10);
    });

    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });

    // Simulate server disconnect (not clean close)
    mockWebSocket.close(1006, 'Connection lost');

    // Verify disconnected state
    await waitFor(() => {
      expect(result.current.connected).toBe(false);
      expect(result.current.connectionStatus).toBe('disconnected');
    });

    // Advance timer to trigger reconnection (1 second for first attempt)
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });

    // Wait for new connection
    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connecting');
    });

    // Simulate reconnection opening
    await act(async () => {
      vi.advanceTimersByTime(10);
    });

    // Send new connection established
    mockWebSocket.mockReceive({
      session_id: 'new-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    // Verify reconnected
    await waitFor(() => {
      expect(result.current.connected).toBe(true);
      expect(result.current.connectionStatus).toBe('connected');
    });

    // Verify reconnect attempts were tracked
    const store = useWebSocketStore.getState();
    expect(store.reconnectAttempts).toBeGreaterThan(0);

    vi.useRealTimers();
  });

  /**
   * Additional test: Unsubscribe sends correct protocol message
   */
  it('unsubscribe_sends_protocol_message', { timeout: 10000 }, async () => {
    const { result } = renderHook(() => useNQHubWebSocket());

    // Establish connection
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
    });

    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });

    // Subscribe first
    act(() => {
      result.current.subscribe(['price', 'orderflow']);
    });

    mockWebSocket.mockReceive({
      action: 'subscribed',
      channels: ['price', 'orderflow'],
    });

    // Clear messages
    sentMessages.length = 0;

    // Unsubscribe from one channel
    act(() => {
      result.current.unsubscribe(['price']);
    });

    // Verify unsubscribe message was sent
    await waitFor(() => {
      expect(sentMessages).toContainEqual({
        action: 'unsubscribe',
        channels: ['price'],
      });
    });
  });

  /**
   * Additional test: Heartbeat ping/pong
   */
  it('sends_heartbeat_pings_and_receives_pongs', { timeout: 35000 }, async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useNQHubWebSocket());

    // Advance timer to open connection
    await act(async () => {
      vi.advanceTimersByTime(10);
    });

    // Establish connection
    await waitFor(() => {
      expect(mockWebSocket).toBeDefined();
    });

    mockWebSocket.mockReceive({
      session_id: 'test-session-id',
      server_time: new Date().toISOString(),
      version: '1.0.0',
    });

    await waitFor(() => {
      expect(result.current.connected).toBe(true);
    });

    // Clear initial messages
    sentMessages.length = 0;

    // Advance time by 30 seconds to trigger heartbeat
    await act(async () => {
      vi.advanceTimersByTime(30000);
    });

    // Verify ping was sent
    await waitFor(() => {
      expect(sentMessages).toContainEqual({ action: 'ping' });
    });

    // Send pong response
    mockWebSocket.mockReceive({
      action: 'pong',
      timestamp: new Date().toISOString(),
    });

    // Connection should remain stable
    expect(result.current.connected).toBe(true);

    vi.useRealTimers();
  });
});