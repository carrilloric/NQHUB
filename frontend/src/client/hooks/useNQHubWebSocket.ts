/**
 * WebSocket Client Hook for NQHUB
 *
 * Based on CONTRACT-005 WebSocket specification
 * Provides real-time connection to 8 WebSocket channels
 */

import { useEffect, useRef, useCallback } from 'react';
import { useWebSocketStore, Channel, WsMessage } from '@/state/websocket.store';
import { useAuth } from '@/state/app';

// Configuration
const WS_ENDPOINT = import.meta.env.DEV
  ? 'ws://localhost:8002/ws/live'
  : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/live`;

// Exponential backoff configuration
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000]; // max 30s
const MAX_RECONNECT_ATTEMPTS = 10;

export interface UseNQHubWebSocketReturn {
  connected: boolean;
  subscribe: (channels: Channel[]) => void;
  unsubscribe: (channels: Channel[]) => void;
  lastMessage: Record<Channel, WsMessage | null>;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
}

/**
 * Hook for WebSocket connection to NQHUB backend
 *
 * Features:
 * - Auto-connects on mount with JWT token
 * - Exponential backoff reconnection
 * - Subscribe/unsubscribe protocol per CONTRACT-005
 * - Throttling: price channel max 10 messages/sec
 * - Risk channel never throttled
 * - Clean disconnect on unmount
 */
export function useNQHubWebSocket(): UseNQHubWebSocketReturn {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const heartbeatInterval = useRef<NodeJS.Timeout | null>(null);

  const { token } = useAuth();

  const {
    connected,
    connectionStatus,
    lastMessage,
    subscribedChannels,
    reconnectAttempts,
    // Actions
    setConnected,
    setConnectionStatus,
    setSessionId,
    setServerVersion,
    setSubscribedChannels,
    addSubscribedChannel,
    removeSubscribedChannel,
    setLastMessage,
    addMessageToHistory,
    setLastError,
    incrementReconnectAttempts,
    resetReconnectAttempts,
    reset,
  } = useWebSocketStore();

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Don't connect without token
    if (!token) {
      console.warn('[WebSocket] No auth token available, skipping connection');
      return;
    }

    // Don't create duplicate connections
    if (ws.current?.readyState === WebSocket.CONNECTING ||
        ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    console.log('[WebSocket] Connecting to', WS_ENDPOINT);
    setConnectionStatus('connecting');

    // Create WebSocket connection with JWT token
    const wsUrl = `${WS_ENDPOINT}?token=${encodeURIComponent(token)}`;
    ws.current = new WebSocket(wsUrl);

    // Connection opened
    ws.current.onopen = () => {
      console.log('[WebSocket] Connection established');
      setConnected(true);
      setConnectionStatus('connected');
      resetReconnectAttempts();
      setLastError(null);

      // Start heartbeat (every 30 seconds per CONTRACT-005)
      heartbeatInterval.current = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ action: 'ping' }));
        }
      }, 30000);
    };

    // Handle incoming messages
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle connection established message
        if (data.session_id && data.server_time && data.version) {
          console.log('[WebSocket] Session established:', data.session_id);
          setSessionId(data.session_id);
          setServerVersion(data.version);
          return;
        }

        // Handle control messages
        if (data.action === 'subscribed') {
          console.log('[WebSocket] Subscribed to channels:', data.channels);
          setSubscribedChannels(data.channels);
          return;
        }

        if (data.action === 'unsubscribed') {
          console.log('[WebSocket] Unsubscribed from channels:', data.channels);
          // Get current channels from store instead of using stale closure
          const store = useWebSocketStore.getState();
          const newChannels = store.subscribedChannels.filter(
            ch => !data.channels.includes(ch)
          );
          setSubscribedChannels(newChannels);
          return;
        }

        // Handle data messages (must have channel, event, data, timestamp per CONTRACT-005)
        if (data.channel && data.event && data.data && data.timestamp) {
          const message: WsMessage = {
            channel: data.channel,
            event: data.event,
            data: data.data,
            timestamp: data.timestamp,
            bot_id: data.bot_id,
          };

          // Update last message (store handles throttling)
          setLastMessage(data.channel, message);

          // Add to history
          addMessageToHistory(message);
        }
      } catch (error) {
        console.error('[WebSocket] Error parsing message:', error);
      }
    };

    // Handle errors
    ws.current.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      setConnectionStatus('error');
      setLastError('WebSocket connection error');
    };

    // Handle connection close
    ws.current.onclose = (event) => {
      console.log('[WebSocket] Connection closed:', event.code, event.reason);
      setConnected(false);
      setConnectionStatus('disconnected');
      setSessionId(null);
      setServerVersion(null);
      setSubscribedChannels([]);

      // Clear heartbeat
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
        heartbeatInterval.current = null;
      }

      // Get current state from store to avoid stale closure
      const store = useWebSocketStore.getState();

      // Attempt reconnection if not intentionally closed
      if (event.code !== 1000 && store.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAYS[Math.min(store.reconnectAttempts, RECONNECT_DELAYS.length - 1)];
        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${store.reconnectAttempts + 1})`);

        incrementReconnectAttempts();
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, delay);
      }
    };
  }, [
    token,
    setConnected,
    setConnectionStatus,
    setSessionId,
    setServerVersion,
    setSubscribedChannels,
    setLastMessage,
    addMessageToHistory,
    setLastError,
    incrementReconnectAttempts,
    resetReconnectAttempts,
  ]);

  /**
   * Subscribe to channels
   */
  const subscribe = useCallback((channels: Channel[]) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] Cannot subscribe: not connected');
      return;
    }

    // Filter out already subscribed channels
    const newChannels = channels.filter(ch => !subscribedChannels.includes(ch));
    if (newChannels.length === 0) {
      console.log('[WebSocket] Already subscribed to all requested channels');
      return;
    }

    console.log('[WebSocket] Subscribing to channels:', newChannels);
    ws.current.send(JSON.stringify({
      action: 'subscribe',
      channels: newChannels,
    }));

    // Optimistically update local state
    newChannels.forEach(addSubscribedChannel);
  }, [subscribedChannels, addSubscribedChannel]);

  /**
   * Unsubscribe from channels
   */
  const unsubscribe = useCallback((channels: Channel[]) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] Cannot unsubscribe: not connected');
      return;
    }

    // Filter to only subscribed channels
    const channelsToUnsubscribe = channels.filter(ch => subscribedChannels.includes(ch));
    if (channelsToUnsubscribe.length === 0) {
      console.log('[WebSocket] Not subscribed to any requested channels');
      return;
    }

    console.log('[WebSocket] Unsubscribing from channels:', channelsToUnsubscribe);
    ws.current.send(JSON.stringify({
      action: 'unsubscribe',
      channels: channelsToUnsubscribe,
    }));

    // Optimistically update local state
    channelsToUnsubscribe.forEach(removeSubscribedChannel);
  }, [subscribedChannels, removeSubscribedChannel]);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    console.log('[WebSocket] Disconnecting...');

    // Clear reconnection timeout
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    // Clear heartbeat
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
      heartbeatInterval.current = null;
    }

    // Close WebSocket connection
    if (ws.current) {
      ws.current.close(1000, 'Client disconnect');
      ws.current = null;
    }

    // Reset store state
    reset();
  }, [reset]);

  /**
   * Auto-connect on mount and disconnect on unmount
   */
  useEffect(() => {
    // Only connect if we have a token
    if (token) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]); // Only reconnect when token changes, not on every render

  return {
    connected,
    subscribe,
    unsubscribe,
    lastMessage,
    connectionStatus,
  };
}