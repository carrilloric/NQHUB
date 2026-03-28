/**
 * Live Dashboard Page
 *
 * Real-time trading dashboard with WebSocket data
 * Shows P&L, positions, equity curve, and candlestick chart
 */

import React, { useEffect, useState } from 'react';
import { useNQHubWebSocket } from '@/hooks/useNQHubWebSocket';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  WifiIcon,
  WifiOffIcon,
  RefreshCwIcon
} from 'lucide-react';
import { cn } from '@/lib/utils';
import PnLCard from '@/components/live-dashboard/PnLCard';
import EquityCurve from '@/components/live-dashboard/EquityCurve';
import PositionsTable from '@/components/live-dashboard/PositionsTable';
import CandlestickChart from '@/components/live-dashboard/CandlestickChart';
import ConnectionStatus from '@/components/live-dashboard/ConnectionStatus';

export default function LiveDashboard() {
  const {
    connected,
    subscribe,
    unsubscribe,
    lastMessage,
    connectionStatus
  } = useNQHubWebSocket();

  const [selectedTimeframe, setSelectedTimeframe] = useState('1min');

  // Subscribe to all required channels on mount
  useEffect(() => {
    const channels = [
      'price',
      'orderflow',
      'patterns',
      'orders',
      'positions',
      'portfolio',
      'risk',
      'bot'
    ] as const;

    subscribe([...channels]);

    // Cleanup: unsubscribe on unmount
    return () => {
      unsubscribe([...channels]);
    };
  }, [subscribe, unsubscribe]);

  // Extract data from last messages
  const portfolioData = lastMessage.portfolio?.data as any;
  const positionsData = lastMessage.positions?.data as any;
  const priceData = lastMessage.price?.data as any;
  const patternsData = lastMessage.patterns?.data as any;
  const botData = lastMessage.bot?.data as any;
  const riskData = lastMessage.risk?.data as any;

  return (
    <div className="container mx-auto p-4 space-y-4">
      {/* Header with Connection Status */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Live Dashboard</h1>
          <p className="text-muted-foreground">Real-time trading metrics and positions</p>
        </div>
        <ConnectionStatus
          status={connectionStatus}
          botName={botData?.bot_name || 'NQ Bot'}
          mode={botData?.mode || 'paper'}
        />
      </div>

      {/* Top Row: P&L Card and Equity Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PnLCard
          balance={portfolioData?.balance || 0}
          equity={portfolioData?.equity || 0}
          unrealizedPnL={portfolioData?.unrealized_pnl || 0}
          realizedPnLToday={portfolioData?.realized_pnl_today || 0}
          dailyTrades={portfolioData?.daily_trades || 0}
          winRate={portfolioData?.win_rate || 0}
          maxDrawdown={portfolioData?.max_drawdown || 0}
        />

        <EquityCurve
          data={portfolioData?.equity_curve || []}
          drawdown={portfolioData?.drawdown_series || []}
        />
      </div>

      {/* Middle Row: Open Positions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Open Positions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <PositionsTable
            positions={positionsData ? [positionsData] : []}
          />
        </CardContent>
      </Card>

      {/* Bottom Row: Candlestick Chart with SMC Overlays */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              NQ Futures Chart
            </CardTitle>
            <Tabs value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
              <TabsList>
                <TabsTrigger value="1min">1 Min</TabsTrigger>
                <TabsTrigger value="5min">5 Min</TabsTrigger>
                <TabsTrigger value="15min">15 Min</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        <CardContent>
          <CandlestickChart
            timeframe={selectedTimeframe}
            priceData={priceData}
            patterns={patternsData}
          />
        </CardContent>
      </Card>

      {/* Risk Alerts (if any) */}
      {riskData && (
        <Card className="border-red-500 bg-red-50 dark:bg-red-950/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertTriangle className="w-5 h-5" />
              Risk Alert
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600 dark:text-red-400">
              {riskData.message || 'Risk limit exceeded'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}