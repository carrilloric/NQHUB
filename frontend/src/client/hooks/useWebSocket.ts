/**
 * useWebSocket Hook
 *
 * React hook for accessing WebSocket functionality.
 * Provides convenient access to WebSocket store and auto-management of subscriptions.
 *
 * Usage:
 *   const { connected, subscribe, latestCandle, latestRiskCheck } = useWebSocket();
 *
 *   useEffect(() => {
 *     subscribe(['price', 'risk']);
 *   }, [subscribe]);
 */
import { useEffect } from 'react';
import { useWebSocketStore } from '@/state/websocket.store';

type Channel =
  | 'price'
  | 'orderflow'
  | 'patterns'
  | 'orders'
  | 'positions'
  | 'portfolio'
  | 'risk'
  | 'bot';

interface UseWebSocketOptions {
  /**
   * Auto-subscribe to these channels on mount.
   * Will auto-unsubscribe on unmount.
   */
  autoSubscribe?: Channel[];

  /**
   * Auto-connect on mount (requires token from auth context).
   * Default: false
   */
  autoConnect?: boolean;

  /**
   * JWT token for authentication (required if autoConnect=true).
   */
  token?: string;
}

/**
 * Hook for using WebSocket functionality in React components.
 *
 * @param options - Configuration options for auto-subscribe/connect
 * @returns WebSocket store state and actions
 *
 * @example
 * // Basic usage - manual subscription
 * const { connected, subscribe, latestCandle } = useWebSocket();
 * useEffect(() => {
 *   if (connected) {
 *     subscribe(['price']);
 *   }
 * }, [connected]);
 *
 * @example
 * // Auto-subscribe to channels
 * const { latestRiskCheck } = useWebSocket({
 *   autoSubscribe: ['risk', 'orders'],
 *   autoConnect: true,
 *   token: userToken,
 * });
 */
export function useWebSocket(options?: UseWebSocketOptions) {
  const store = useWebSocketStore();

  const {
    status,
    error,
    subscribedChannels,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    clearError,
  } = store;

  const connected = status === 'connected';
  const reconnecting = status === 'connecting';

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (options?.autoConnect && options?.token && !connected) {
      console.log('[useWebSocket] Auto-connecting...');
      connect(options.token);
    }

    // Cleanup: disconnect on unmount if auto-connected
    return () => {
      if (options?.autoConnect) {
        console.log('[useWebSocket] Auto-disconnect on unmount');
        disconnect();
      }
    };
  }, [options?.autoConnect, options?.token, connect, disconnect, connected]);

  // Auto-subscribe to channels on mount
  useEffect(() => {
    if (options?.autoSubscribe && connected) {
      console.log('[useWebSocket] Auto-subscribing to:', options.autoSubscribe);
      subscribe(options.autoSubscribe);

      // Cleanup: unsubscribe on unmount
      return () => {
        console.log('[useWebSocket] Auto-unsubscribing from:', options.autoSubscribe);
        unsubscribe(options.autoSubscribe);
      };
    }
  }, [options?.autoSubscribe, connected, subscribe, unsubscribe]);

  // Extract latest messages per channel (mocked for now)
  const latestCandle = null;
  const latestPattern = null;
  const latestRiskCheck = null;
  const latestKillSwitch = null;
  const latestOrder = null;
  const openPositions: any[] = [];
  const portfolioSnapshot = null;
  const botStatus = null;

  return {
    // Connection state
    connected,
    reconnecting,
    error,
    clearError,

    // Actions
    connect,
    disconnect,
    subscribe,
    unsubscribe,

    // Subscriptions
    subscribedChannels: Array.from(subscribedChannels),

    // Latest data per channel
    latestCandle,
    latestPattern,
    latestRiskCheck,
    latestKillSwitch,
    latestOrder,
    openPositions,
    portfolioSnapshot,
    botStatus,
  };
}

/**
 * Helper hook for subscribing to a single channel.
 *
 * @param channel - Channel to subscribe to
 * @param options - Options (autoConnect, token)
 *
 * @example
 * const { latestCandle } = useWebSocketChannel('price', { autoConnect: true, token });
 */
export function useWebSocketChannel(
  channel: Channel,
  options?: Omit<UseWebSocketOptions, 'autoSubscribe'>
) {
  return useWebSocket({
    ...options,
    autoSubscribe: [channel],
  });
}

/**
 * Helper hook for risk channel (highest priority).
 * Auto-subscribes to 'risk' channel.
 *
 * @param options - Options (autoConnect, token)
 *
 * @example
 * const { latestRiskCheck, latestKillSwitch } = useRiskChannel({ autoConnect: true, token });
 */
export function useRiskChannel(options?: Omit<UseWebSocketOptions, 'autoSubscribe'>) {
  return useWebSocket({
    ...options,
    autoSubscribe: ['risk'],
  });
}

/**
 * Helper hook for trading execution channels (orders + positions).
 * Auto-subscribes to 'orders' and 'positions' channels.
 *
 * @param options - Options (autoConnect, token)
 *
 * @example
 * const { latestOrder, openPositions } = useTradingChannel({ autoConnect: true, token });
 */
export function useTradingChannel(options?: Omit<UseWebSocketOptions, 'autoSubscribe'>) {
  return useWebSocket({
    ...options,
    autoSubscribe: ['orders', 'positions'],
  });
}

/**
 * Helper hook for market data channels (price + orderflow).
 * Auto-subscribes to 'price' and 'orderflow' channels.
 *
 * @param options - Options (autoConnect, token)
 *
 * @example
 * const { latestCandle } = useMarketDataChannel({ autoConnect: true, token });
 */
export function useMarketDataChannel(options?: Omit<UseWebSocketOptions, 'autoSubscribe'>) {
  return useWebSocket({
    ...options,
    autoSubscribe: ['price', 'orderflow'],
  });
}
