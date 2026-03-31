import { useState, useCallback, useRef } from 'react';
import { apiClient } from '@/services/api';

export interface BacktestConfig {
  strategy_id: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  timeframe: '1min' | '5min' | '15min' | '1h';
  commission_per_side: number;
  slippage_ticks: number;
  symbol?: string;
}

export interface BacktestMetrics {
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  total_return: number;
  annual_return: number;
  calmar_ratio: number;
  recovery_factor: number;
}

export interface ApexCompliance {
  compliant: boolean;
  trailing_threshold: {
    value: number;
    max_allowed: number;
    passed: boolean;
  };
  max_contracts: {
    value: number;
    max_allowed: number;
    passed: boolean;
  };
  trading_hours: {
    compliant: boolean;
    violations: string[];
  };
  profit_goal: {
    value: number;
    target: number;
    passed: boolean;
  };
}

export interface BacktestResult {
  backtest_id: string;
  strategy_id: string;
  strategy_name: string;
  status: 'completed' | 'failed' | 'running';
  metrics: BacktestMetrics;
  apex_compliance: ApexCompliance;
  equity_curve: Array<{
    timestamp: string;
    equity: number;
    drawdown: number;
  }>;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface BacktestTrade {
  trade_id: number;
  entry_time: string;
  exit_time: string;
  side: 'LONG' | 'SHORT';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  commission: number;
  slippage: number;
  net_pnl: number;
  cumulative_pnl: number;
}

const POLLING_INTERVAL = 2000; // 2 seconds
const POLLING_TIMEOUT = 300000; // 5 minutes

export function useBacktest() {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  const clearPollingTimeout = useCallback(() => {
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
      pollingTimeoutRef.current = null;
    }
  }, []);

  const pollBacktestStatus = useCallback(async (taskId: string): Promise<void> => {
    const checkStatus = async () => {
      try {
        // Check if we've exceeded the timeout
        if (startTimeRef.current && Date.now() - startTimeRef.current > POLLING_TIMEOUT) {
          setError('Backtest timeout: exceeded 5 minutes');
          setIsRunning(false);
          clearPollingTimeout();
          return;
        }

        const response = await apiClient.get(`/api/v1/backtest/status/${taskId}`);
        const data = await response.json();

        if (data.status === 'completed') {
          setProgress(100);
          // Fetch the full results
          const resultsResponse = await apiClient.get(`/api/v1/backtest/screener?id=${data.backtest_id}`);
          const resultsData = await resultsResponse.json();

          if (resultsData.results && resultsData.results.length > 0) {
            setResults(resultsData.results[0]);
          }
          setIsRunning(false);
          clearPollingTimeout();
        } else if (data.status === 'failed') {
          setError(data.error_message || 'Backtest failed');
          setIsRunning(false);
          clearPollingTimeout();
        } else {
          // Still running, update progress
          setProgress(data.progress || 50);
          // Continue polling
          pollingTimeoutRef.current = setTimeout(checkStatus, POLLING_INTERVAL);
        }
      } catch (err) {
        console.error('Error polling backtest status:', err);
        setError('Failed to check backtest status');
        setIsRunning(false);
        clearPollingTimeout();
      }
    };

    await checkStatus();
  }, [apiClient, clearPollingTimeout]);

  const runBacktest = useCallback(async (config: BacktestConfig): Promise<string | null> => {
    setIsRunning(true);
    setProgress(0);
    setError(null);
    setResults(null);
    startTimeRef.current = Date.now();

    try {
      // Default to NQ if no symbol specified
      const backtestPayload = {
        ...config,
        symbol: config.symbol || 'NQ',
        tick_size: 0.25,
        tick_value: 5,
        point_value: 20,
      };

      const response = await apiClient.post('/api/v1/backtest/run', backtestPayload);
      const data = await response.json();

      if (data.task_id) {
        setProgress(10);
        // Start polling for status
        await pollBacktestStatus(data.task_id);
        return data.task_id;
      } else {
        throw new Error('No task ID returned from backtest run');
      }
    } catch (err) {
      console.error('Error running backtest:', err);
      setError(err instanceof Error ? err.message : 'Failed to run backtest');
      setIsRunning(false);
      return null;
    }
  }, [apiClient, pollBacktestStatus]);

  const getBacktestTrades = useCallback(async (
    backtestId: string,
    page = 1,
    pageSize = 50
  ): Promise<{ trades: BacktestTrade[]; total: number }> => {
    try {
      const response = await apiClient.get(
        `/api/v1/backtest/${backtestId}/trades?page=${page}&page_size=${pageSize}`
      );
      const data = await response.json();
      return {
        trades: data.trades || [],
        total: data.total || 0,
      };
    } catch (err) {
      console.error('Error fetching backtest trades:', err);
      return { trades: [], total: 0 };
    }
  }, [apiClient]);

  const getStrategies = useCallback(async (): Promise<Array<{ id: string; name: string; description: string }>> => {
    try {
      const response = await apiClient.get('/api/v1/strategies');
      const data = await response.json();
      return data.strategies || [];
    } catch (err) {
      console.error('Error fetching strategies:', err);
      return [];
    }
  }, [apiClient]);

  const compareBacktests = useCallback(async (
    backtestIds: string[]
  ): Promise<BacktestResult[]> => {
    try {
      const ids = backtestIds.join(',');
      const response = await apiClient.get(`/api/v1/backtest/compare?ids=${ids}`);
      const data = await response.json();
      return data.results || [];
    } catch (err) {
      console.error('Error comparing backtests:', err);
      return [];
    }
  }, [apiClient]);

  const exportBacktestData = useCallback(async (
    backtestId: string,
    format: 'csv' | 'json' = 'csv'
  ): Promise<Blob | null> => {
    try {
      const response = await apiClient.get(
        `/api/v1/backtest/${backtestId}/export?format=${format}`
      );
      return await response.blob();
    } catch (err) {
      console.error('Error exporting backtest data:', err);
      return null;
    }
  }, [apiClient]);

  return {
    runBacktest,
    getBacktestTrades,
    getStrategies,
    compareBacktests,
    exportBacktestData,
    isRunning,
    progress,
    results,
    error,
  };
}