/**
 * useLiveDashboard Hook
 *
 * Manages WebSocket subscriptions and state for the Live Dashboard.
 * Subscribes to 6 channels: price, positions, portfolio, risk, orders, patterns
 *
 * Returns real-time data for:
 * - Latest candle (price channel)
 * - Open positions (positions channel)
 * - Portfolio snapshot (portfolio channel)
 * - Risk status (risk channel)
 * - Recent orders (orders channel)
 * - Detected patterns (patterns channel)
 */
import { useEffect, useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import type {
  CandleEvent,
  PositionEvent,
  PortfolioSnapshot,
  RiskCheckEvent,
  OrderEvent,
  PatternEvent,
} from '@/stores/websocketStore';

interface LiveDashboardData {
  latestCandle: CandleEvent | null;
  openPositions: PositionEvent[];
  portfolio: PortfolioSnapshot | null;
  riskStatus: RiskCheckEvent | null;
  recentOrders: OrderEvent[];
  patterns: PatternEvent[];
  connected: boolean;
  error: string | null;
}

export function useLiveDashboard(botId?: string): LiveDashboardData {
  const {
    connected,
    error,
    latestCandle,
    latestPattern,
    latestRiskCheck,
    latestOrder,
    openPositions,
    portfolioSnapshot,
    subscribe,
  } = useWebSocket({
    autoSubscribe: ['price', 'positions', 'portfolio', 'risk', 'orders', 'patterns'],
  });

  // Store recent orders (last 10)
  const [recentOrders, setRecentOrders] = useState<OrderEvent[]>([]);

  // Store detected patterns
  const [patterns, setPatterns] = useState<PatternEvent[]>([]);

  // Update recent orders when new order arrives
  useEffect(() => {
    if (latestOrder) {
      setRecentOrders((prev) => {
        const newOrders = [latestOrder, ...prev];
        return newOrders.slice(0, 10); // Keep only last 10
      });
    }
  }, [latestOrder]);

  // Update patterns when new pattern arrives
  useEffect(() => {
    if (latestPattern) {
      setPatterns((prev) => {
        const newPatterns = [latestPattern, ...prev];
        return newPatterns.slice(0, 20); // Keep only last 20
      });
    }
  }, [latestPattern]);

  return {
    latestCandle,
    openPositions,
    portfolio: portfolioSnapshot,
    riskStatus: latestRiskCheck,
    recentOrders,
    patterns,
    connected,
    error,
  };
}
