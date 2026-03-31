/**
 * useBotManagement Hook (AUT-354)
 *
 * Custom hook for bot management operations:
 * - Fetch bots list
 * - Fetch state logs
 * - Start/Stop/Kill operations
 * - Create new bots
 * - WebSocket real-time updates
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import type { BotStatus } from '@/client/components/bots/StatusBadge';

interface Bot {
  id: string;
  name: string;
  strategy_id: string;
  status: BotStatus;
  mode: 'live' | 'paper';
  last_heartbeat: string;
  apex_account_id: string | null;
  active_params: Record<string, any>;
  daily_pnl: number;
  open_contracts: number;
}

interface StateLogEntry {
  from: BotStatus;
  to: BotStatus;
  reason: string;
  timestamp: string;
}

interface UseBotManagementReturn {
  bots: Bot[];
  stateLogs: Record<string, StateLogEntry[]>;
  isLoading: boolean;
  error: string | null;
  fetchBots: () => Promise<void>;
  fetchStateLog: (botId: string) => Promise<void>;
  startBot: (botId: string) => Promise<void>;
  stopBot: (botId: string) => Promise<void>;
  killBot: (botId: string, reason: string) => Promise<void>;
  createBot: (data: {
    name: string;
    strategy_id: string;
    mode: 'live' | 'paper';
    apex_account_id?: string;
  }) => Promise<void>;
}

export function useBotManagement(): UseBotManagementReturn {
  const [bots, setBots] = useState<Bot[]>([]);
  const [stateLogs, setStateLogs] = useState<Record<string, StateLogEntry[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Subscribe to 'bot' channel for real-time updates
  const { botStatus, connected } = useWebSocket({
    autoSubscribe: ['bot'],
  });

  /**
   * Fetch all bots
   */
  const fetchBots = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/v1/bots');
      if (!response.ok) {
        throw new Error('Failed to fetch bots');
      }

      const data = await response.json();
      setBots(data.bots);

      // Fetch state logs for each bot
      for (const bot of data.bots) {
        await fetchStateLog(bot.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching bots:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch state log for a specific bot
   */
  const fetchStateLog = useCallback(async (botId: string) => {
    try {
      const response = await fetch(`/api/v1/bots/${botId}/state-log?limit=5`);
      if (!response.ok) {
        throw new Error('Failed to fetch state log');
      }

      const data = await response.json();
      setStateLogs((prev) => ({
        ...prev,
        [botId]: data.states,
      }));
    } catch (err) {
      console.error(`Error fetching state log for bot ${botId}:`, err);
    }
  }, []);

  /**
   * Start a bot
   */
  const startBot = useCallback(async (botId: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/bots/${botId}/start`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start bot');
      }

      // Refresh bots list
      await fetchBots();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error starting bot:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchBots]);

  /**
   * Stop a bot
   */
  const stopBot = useCallback(async (botId: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/bots/${botId}/stop`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to stop bot');
      }

      // Refresh bots list
      await fetchBots();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error stopping bot:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchBots]);

  /**
   * Kill a bot (emergency stop)
   */
  const killBot = useCallback(async (botId: string, reason: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/bots/${botId}/kill`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to kill bot');
      }

      // Refresh bots list
      await fetchBots();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error killing bot:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchBots]);

  /**
   * Create a new bot
   */
  const createBot = useCallback(async (data: {
    name: string;
    strategy_id: string;
    mode: 'live' | 'paper';
    apex_account_id?: string;
  }) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/v1/bots/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: data.name,
          strategy_id: data.strategy_id,
          mode: data.mode,
          apex_account_id: data.apex_account_id || null,
          active_params: {},
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create bot');
      }

      // Refresh bots list
      await fetchBots();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error creating bot:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchBots]);

  /**
   * Handle WebSocket bot status updates
   */
  useEffect(() => {
    if (botStatus && connected) {
      console.log('[useBotManagement] Received bot status update:', botStatus);

      // Update bot in list
      setBots((prevBots) =>
        prevBots.map((bot) =>
          bot.id === botStatus.bot_id
            ? { ...bot, status: botStatus.status, last_heartbeat: botStatus.last_heartbeat }
            : bot
        )
      );

      // Refresh state log for updated bot
      if (botStatus.bot_id) {
        fetchStateLog(botStatus.bot_id);
      }
    }
  }, [botStatus, connected, fetchStateLog]);

  /**
   * Initial fetch on mount
   */
  useEffect(() => {
    fetchBots();
  }, [fetchBots]);

  return {
    bots,
    stateLogs,
    isLoading,
    error,
    fetchBots,
    fetchStateLog,
    startBot,
    stopBot,
    killBot,
    createBot,
  };
}
