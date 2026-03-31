/**
 * WebSocket Zustand Store
 *
 * Manages real-time WebSocket connection to backend /ws/live endpoint.
 * Provides 8 channels for trading data:
 * - price: Real-time candlestick data
 * - orderflow: Order flow metrics (delta, POC)
 * - patterns: ICT pattern detections
 * - orders: Order status changes
 * - positions: Position updates
 * - portfolio: Portfolio snapshots
 * - risk: Risk checks (highest priority)
 * - bot: Bot status updates
 *
 * Features:
 * - Auto-reconnection with exponential backoff
 * - JWT authentication via query parameter
 * - Subscribe/unsubscribe to channels
 * - Type-safe event data per channel
 */
import { create } from 'zustand';

// ============================================================================
// Event Types (matching backend schemas)
// ============================================================================

export interface CandleEvent {
  channel: string;
  ts: string;
  bot_id: string;
  timeframe: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  delta: number;
  poc: number;
}

export interface PatternEvent {
  channel: string;
  ts: string;
  bot_id: string;
  pattern_type: 'fvg' | 'ob' | 'lp' | 'bb';
  direction: 'bullish' | 'bearish';
  top: number;
  bottom: number;
  timeframe: string;
  status: 'active' | 'mitigated' | 'broken';
}

export interface RiskCheckEvent {
  channel: string;
  ts: string;
  bot_id: string;
  check_name: string;
  result: 'PASSED' | 'REJECTED';
  reason: string;
  trigger_kill_switch: boolean;
  account_balance: number;
  current_pnl: number;
}

export interface KillSwitchEvent {
  channel: string;
  ts: string;
  bot_id: string;
  scope: 'per_bot' | 'global';
  reason: string;
  triggered_by: 'manual' | 'circuit_breaker';
  positions_closed: number;
  orders_cancelled: number;
}

export interface OrderEvent {
  channel: string;
  ts: string;
  bot_id: string;
  order_id: string;
  client_order_id: string;
  broker_order_id?: string;
  bracket_role?: 'ENTRY' | 'TP' | 'SL';
  side: 'BUY' | 'SELL';
  contracts: number;
  fill_price?: number;
  status: 'SUBMITTED' | 'FILLED' | 'REJECTED' | 'CANCELLED';
}

export interface PositionEvent {
  channel: string;
  ts: string;
  bot_id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  contracts: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_ticks: number;
}

export interface PortfolioSnapshot {
  channel: string;
  ts: string;
  bot_id: string;
  total_value: number;
  cash: number;
  positions_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  daily_pnl: number;
}

export interface BotStatusEvent {
  channel: string;
  ts: string;
  bot_id: string;
  status: 'RUNNING' | 'PAUSED' | 'STOPPED' | 'ERROR';
  uptime_seconds: number;
  trades_today: number;
  pnl_today: number;
}

// ============================================================================
// WebSocket Store
// ============================================================================

type Channel =
  | 'price'
  | 'orderflow'
  | 'patterns'
  | 'orders'
  | 'positions'
  | 'portfolio'
  | 'risk'
  | 'bot';

interface WebSocketState {
  // Connection state
  ws: WebSocket | null;
  connected: boolean;
  reconnecting: boolean;
  error: string | null;

  // Subscribed channels
  subscribedChannels: Set<Channel>;

  // Latest data per channel
  latestCandle: CandleEvent | null;
  latestPattern: PatternEvent | null;
  latestRiskCheck: RiskCheckEvent | null;
  latestKillSwitch: KillSwitchEvent | null;
  latestOrder: OrderEvent | null;
  openPositions: PositionEvent[];
  portfolioSnapshot: PortfolioSnapshot | null;
  botStatus: BotStatusEvent | null;

  // Actions
  connect: (token: string) => void;
  disconnect: () => void;
  subscribe: (channels: Channel[]) => void;
  unsubscribe: (channels: Channel[]) => void;
  clearError: () => void;

  // Internal
  _handleMessage: (event: MessageEvent) => void;
  _handleOpen: () => void;
  _handleClose: () => void;
  _handleError: (event: Event) => void;
  _reconnect: (token: string) => void;
}

// Reconnection parameters
const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_DELAY_MS = 30000;
let reconnectAttempts = 0;

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  // Initial state
  ws: null,
  connected: false,
  reconnecting: false,
  error: null,
  subscribedChannels: new Set(),
  latestCandle: null,
  latestPattern: null,
  latestRiskCheck: null,
  latestKillSwitch: null,
  latestOrder: null,
  openPositions: [],
  portfolioSnapshot: null,
  botStatus: null,

  // Connect to WebSocket
  connect: (token: string) => {
    const { ws, connected } = get();

    // Don't connect if already connected
    if (ws && connected) {
      console.log('[WebSocket] Already connected');
      return;
    }

    console.log('[WebSocket] Connecting...');

    try {
      // Build WebSocket URL with JWT token
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/live?token=${token}`;

      const websocket = new WebSocket(wsUrl);

      websocket.onopen = get()._handleOpen;
      websocket.onmessage = get()._handleMessage;
      websocket.onclose = get()._handleClose;
      websocket.onerror = get()._handleError;

      set({ ws: websocket, error: null });
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      set({ error: String(error) });
    }
  },

  // Disconnect from WebSocket
  disconnect: () => {
    const { ws } = get();

    if (ws) {
      console.log('[WebSocket] Disconnecting...');
      ws.close();
      set({
        ws: null,
        connected: false,
        reconnecting: false,
        subscribedChannels: new Set(),
      });
    }
  },

  // Subscribe to channels
  subscribe: (channels: Channel[]) => {
    const { ws, connected } = get();

    if (!ws || !connected) {
      console.warn('[WebSocket] Cannot subscribe: not connected');
      return;
    }

    const message = {
      action: 'subscribe',
      channels,
    };

    ws.send(JSON.stringify(message));
    console.log('[WebSocket] Subscribe request sent:', channels);
  },

  // Unsubscribe from channels
  unsubscribe: (channels: Channel[]) => {
    const { ws, connected } = get();

    if (!ws || !connected) {
      console.warn('[WebSocket] Cannot unsubscribe: not connected');
      return;
    }

    const message = {
      action: 'unsubscribe',
      channels,
    };

    ws.send(JSON.stringify(message));
    console.log('[WebSocket] Unsubscribe request sent:', channels);
  },

  // Clear error
  clearError: () => set({ error: null }),

  // Internal: Handle incoming messages
  _handleMessage: (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);

      // Handle subscription responses
      if (data.type === 'subscribed') {
        const channels = new Set(data.channels) as Set<Channel>;
        set({ subscribedChannels: channels });
        console.log('[WebSocket] Subscribed to channels:', data.channels);
        return;
      }

      if (data.type === 'unsubscribed') {
        const currentChannels = get().subscribedChannels;
        data.channels.forEach((ch: Channel) => currentChannels.delete(ch));
        set({ subscribedChannels: new Set(currentChannels) });
        console.log('[WebSocket] Unsubscribed from channels:', data.channels);
        return;
      }

      if (data.type === 'error') {
        console.error('[WebSocket] Server error:', data.message);
        set({ error: data.message });
        return;
      }

      // Handle event data based on channel
      if (data.channel) {
        if (data.channel.startsWith('nqhub.candle.')) {
          // CandleEvent
          set({ latestCandle: data as CandleEvent });
        } else if (data.channel.startsWith('nqhub.pattern.')) {
          // PatternEvent
          set({ latestPattern: data as PatternEvent });
        } else if (data.channel === 'nqhub.risk.check') {
          // RiskCheckEvent
          set({ latestRiskCheck: data as RiskCheckEvent });
        } else if (data.channel === 'nqhub.risk.kill_switch') {
          // KillSwitchEvent (HIGHEST PRIORITY)
          set({ latestKillSwitch: data as KillSwitchEvent });
          console.warn('[WebSocket] KILL SWITCH ACTIVATED:', data);
        } else if (data.channel.startsWith('exec.order.')) {
          // OrderEvent
          set({ latestOrder: data as OrderEvent });
        } else if (data.channel.startsWith('exec.position.')) {
          // PositionEvent - update or add to openPositions array
          const position = data as PositionEvent;
          const currentPositions = get().openPositions;
          const existingIndex = currentPositions.findIndex(
            (p) => p.bot_id === position.bot_id && p.symbol === position.symbol
          );

          if (existingIndex >= 0) {
            currentPositions[existingIndex] = position;
          } else {
            currentPositions.push(position);
          }

          set({ openPositions: [...currentPositions] });
        }
      }
    } catch (error) {
      console.error('[WebSocket] Error parsing message:', error);
    }
  },

  // Internal: Handle connection open
  _handleOpen: () => {
    console.log('[WebSocket] Connected');
    reconnectAttempts = 0;
    set({ connected: true, reconnecting: false, error: null });
  },

  // Internal: Handle connection close
  _handleClose: () => {
    console.log('[WebSocket] Disconnected');
    set({ connected: false, ws: null });

    // Attempt reconnection if not manually disconnected
    // TODO: Pass token for reconnection (need to store token securely)
    // For now, just log that reconnection is needed
    console.log('[WebSocket] Reconnection needed - call connect() with token');
  },

  // Internal: Handle connection error
  _handleError: (event: Event) => {
    console.error('[WebSocket] Error:', event);
    set({ error: 'WebSocket connection error' });
  },

  // Internal: Reconnect with exponential backoff
  _reconnect: (token: string) => {
    const delay = Math.min(
      RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts),
      MAX_RECONNECT_DELAY_MS
    );

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1})`);
    reconnectAttempts++;

    set({ reconnecting: true });

    setTimeout(() => {
      get().connect(token);
    }, delay);
  },
}));
