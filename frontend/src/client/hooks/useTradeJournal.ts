/**
 * Hook for Trade Journal data management
 * AUT-356
 */
import { useState, useEffect } from 'react';

export interface TradeFilters {
  bot_id?: string;
  strategy_id?: string;
  direction?: 'LONG' | 'SHORT' | 'ALL';
  start_date?: string;
  end_date?: string;
}

export interface Trade {
  id: string;
  bot_id: string;
  side: 'LONG' | 'SHORT';
  entry_price: number;
  exit_price: number;
  contracts: number;
  gross_pnl: number;
  net_pnl: number;
  duration_seconds: number;
  exit_reason: 'TP_HIT' | 'SL_HIT' | 'TIME' | 'SIGNAL';
  ts: string;
  notes?: string;
  tags?: string[];
}

export interface TradeSummary {
  total_pnl: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  wins: number;
  losses: number;
}

export interface TradeJournalData {
  trades: Trade[];
  summary: TradeSummary;
}

export function useTradeJournal(filters: TradeFilters) {
  const [data, setData] = useState<TradeJournalData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTrades = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (filters.bot_id) params.append('bot_id', filters.bot_id);
        if (filters.strategy_id) params.append('strategy_id', filters.strategy_id);
        if (filters.direction) params.append('direction', filters.direction);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);

        const response = await fetch(`/api/v1/trades?${params.toString()}`);
        if (!response.ok) {
          throw new Error('Failed to fetch trades');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTrades();
  }, [filters.bot_id, filters.strategy_id, filters.direction, filters.start_date, filters.end_date]);

  const updateNotes = async (tradeId: string, notes: string, tags: string[]) => {
    try {
      const response = await fetch(`/api/v1/trades/${tradeId}/notes`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes, tags }),
      });

      if (!response.ok) {
        throw new Error('Failed to update notes');
      }

      // Update local state
      if (data) {
        setData({
          ...data,
          trades: data.trades.map(t =>
            t.id === tradeId ? { ...t, notes, tags } : t
          ),
        });
      }

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    }
  };

  return {
    trades: data?.trades || [],
    summary: data?.summary || {
      total_pnl: 0,
      win_rate: 0,
      profit_factor: 0,
      total_trades: 0,
      wins: 0,
      losses: 0,
    },
    isLoading,
    error,
    updateNotes,
  };
}
