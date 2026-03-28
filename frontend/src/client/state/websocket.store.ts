/**
 * WebSocket Zustand Store
 *
 * Based on CONTRACT-005 WebSocket specification
 * Manages WebSocket connection state and messages for 8 channels
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// WebSocket channels according to CONTRACT-005
export type Channel =
  | 'price'
  | 'orderflow'
  | 'patterns'
  | 'orders'
  | 'positions'
  | 'portfolio'
  | 'risk'
  | 'bot';

// Connection status types
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// WebSocket message format from CONTRACT-005
export interface WsMessage {
  channel: Channel;
  event: string;
  data: unknown;
  timestamp: string;
  bot_id?: string;
}

// Subscribe/unsubscribe request format
export interface SubscribeRequest {
  action: 'subscribe';
  channels: Channel[];
}

export interface UnsubscribeRequest {
  action: 'unsubscribe';
  channels: Channel[];
}

// Control messages
export interface ControlMessage {
  action: 'subscribed' | 'unsubscribed';
  channels: Channel[];
}

// WebSocket store state
export interface WebSocketStore {
  // Connection state
  connected: boolean;
  connectionStatus: ConnectionStatus;
  sessionId: string | null;
  serverVersion: string | null;

  // Subscription state
  subscribedChannels: Channel[];
  pendingSubscriptions: Channel[];

  // Message state
  lastMessage: Record<Channel, WsMessage | null>;
  messageHistory: WsMessage[];

  // Throttling state
  priceThrottleTimestamp: number;
  priceThrottleCount: number;

  // Error state
  lastError: string | null;
  reconnectAttempts: number;

  // Actions
  setConnected: (connected: boolean) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setSessionId: (sessionId: string | null) => void;
  setServerVersion: (version: string | null) => void;

  setSubscribedChannels: (channels: Channel[]) => void;
  addSubscribedChannel: (channel: Channel) => void;
  removeSubscribedChannel: (channel: Channel) => void;
  setPendingSubscriptions: (channels: Channel[]) => void;

  setLastMessage: (channel: Channel, message: WsMessage) => void;
  addMessageToHistory: (message: WsMessage) => void;
  clearMessageHistory: () => void;

  updatePriceThrottle: () => void;
  resetPriceThrottle: () => void;
  shouldThrottlePrice: () => boolean;

  setLastError: (error: string | null) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;

  // Utility actions
  reset: () => void;
  isChannelSubscribed: (channel: Channel) => boolean;
  getMessageCount: (channel: Channel) => number;
}

// Initial state factory
const getInitialState = () => ({
  // Connection state
  connected: false,
  connectionStatus: 'disconnected' as ConnectionStatus,
  sessionId: null,
  serverVersion: null,

  // Subscription state
  subscribedChannels: [] as Channel[],
  pendingSubscriptions: [] as Channel[],

  // Message state
  lastMessage: {
    price: null,
    orderflow: null,
    patterns: null,
    orders: null,
    positions: null,
    portfolio: null,
    risk: null,
    bot: null,
  } as Record<Channel, WsMessage | null>,
  messageHistory: [] as WsMessage[],

  // Throttling state (for price channel - max 10 messages per second)
  priceThrottleTimestamp: 0,
  priceThrottleCount: 0,

  // Error state
  lastError: null,
  reconnectAttempts: 0,
});

// Create the store
export const useWebSocketStore = create<WebSocketStore>()(
  devtools(
    (set, get) => ({
      ...getInitialState(),

      // Connection actions
      setConnected: (connected) => set({ connected }),

      setConnectionStatus: (status) => set({ connectionStatus: status }),

      setSessionId: (sessionId) => set({ sessionId }),

      setServerVersion: (version) => set({ serverVersion: version }),

      // Subscription actions
      setSubscribedChannels: (channels) => set({ subscribedChannels: channels }),

      addSubscribedChannel: (channel) => set((state) => ({
        subscribedChannels: state.subscribedChannels.includes(channel)
          ? state.subscribedChannels
          : [...state.subscribedChannels, channel],
      })),

      removeSubscribedChannel: (channel) => set((state) => ({
        subscribedChannels: state.subscribedChannels.filter(ch => ch !== channel),
      })),

      setPendingSubscriptions: (channels) => set({ pendingSubscriptions: channels }),

      // Message actions
      setLastMessage: (channel, message) => set((state) => {
        // Apply throttling for price channel
        if (channel === 'price' && state.shouldThrottlePrice()) {
          console.log('[WebSocket] Price message throttled');
          return state;
        }

        // Update throttle count if price channel
        if (channel === 'price') {
          state.updatePriceThrottle();
        }

        // Risk channel messages are NEVER throttled
        const newLastMessage = {
          ...state.lastMessage,
          [channel]: message,
        };

        return { lastMessage: newLastMessage };
      }),

      addMessageToHistory: (message) => set((state) => {
        // Keep only last 100 messages in history
        const newHistory = [...state.messageHistory, message];
        if (newHistory.length > 100) {
          newHistory.shift();
        }
        return { messageHistory: newHistory };
      }),

      clearMessageHistory: () => set({ messageHistory: [] }),

      // Throttling actions
      updatePriceThrottle: () => set((state) => {
        const now = Date.now();
        // Reset counter if more than 1 second has passed
        if (now - state.priceThrottleTimestamp > 1000) {
          return {
            priceThrottleTimestamp: now,
            priceThrottleCount: 1,
          };
        }
        // Increment counter
        return {
          priceThrottleCount: state.priceThrottleCount + 1,
        };
      }),

      resetPriceThrottle: () => set({
        priceThrottleTimestamp: 0,
        priceThrottleCount: 0,
      }),

      shouldThrottlePrice: () => {
        const state = get();
        const now = Date.now();

        // Check if we're within the same second
        if (now - state.priceThrottleTimestamp <= 1000) {
          // Throttle if we've exceeded 10 messages per second
          return state.priceThrottleCount >= 10;
        }

        return false;
      },

      // Error handling actions
      setLastError: (error) => set({ lastError: error }),

      incrementReconnectAttempts: () => set((state) => ({
        reconnectAttempts: state.reconnectAttempts + 1,
      })),

      resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),

      // Utility actions
      reset: () => set(getInitialState()),

      isChannelSubscribed: (channel) => {
        const state = get();
        return state.subscribedChannels.includes(channel);
      },

      getMessageCount: (channel) => {
        const state = get();
        return state.messageHistory.filter(msg => msg.channel === channel).length;
      },
    }),
    {
      name: 'websocket-store',
    }
  )
);

// Selector hooks for common use cases
export const useWebSocketConnection = () =>
  useWebSocketStore((state) => ({
    connected: state.connected,
    connectionStatus: state.connectionStatus,
    sessionId: state.sessionId,
  }));

export const useWebSocketChannels = () =>
  useWebSocketStore((state) => ({
    subscribedChannels: state.subscribedChannels,
    pendingSubscriptions: state.pendingSubscriptions,
  }));

export const useWebSocketMessages = (channel: Channel) =>
  useWebSocketStore((state) => ({
    lastMessage: state.lastMessage[channel],
    messageCount: state.getMessageCount(channel),
  }));

export const useWebSocketErrors = () =>
  useWebSocketStore((state) => ({
    lastError: state.lastError,
    reconnectAttempts: state.reconnectAttempts,
  }));