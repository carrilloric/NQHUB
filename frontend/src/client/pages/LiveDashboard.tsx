/**
 * LiveDashboard Page
 *
 * Main live trading dashboard showing:
 * - Real-time P&L and equity curve (D3)
 * - Candlestick chart with SMC overlays (recharts)
 * - Open positions, risk meters, recent orders
 *
 * WebSocket subscriptions: price, positions, portfolio, risk, orders, patterns
 */
import { useState, useEffect } from 'react';
import { useLiveDashboard } from '@/hooks/useLiveDashboard';
import { TopBar } from '@/components/dashboard/TopBar';
import { EquityCurveChart } from '@/components/dashboard/EquityCurveChart';
import { CandlestickChart } from '@/components/dashboard/CandlestickChart';
import { OpenPositions } from '@/components/dashboard/OpenPositions';
import { RiskMeters } from '@/components/dashboard/RiskMeters';
import { RecentOrders } from '@/components/dashboard/RecentOrders';
import type { CandleEvent, PortfolioSnapshot } from '@/stores/websocketStore';

export default function LiveDashboard() {
  const [selectedBot, setSelectedBot] = useState('bot-1');

  const {
    latestCandle,
    openPositions,
    portfolio,
    riskStatus,
    recentOrders,
    patterns,
    connected,
    error,
  } = useLiveDashboard(selectedBot);

  // Store historical candles for chart
  const [candles, setCandles] = useState<CandleEvent[]>([]);

  // Store portfolio snapshots for equity curve
  const [equityData, setEquityData] = useState<PortfolioSnapshot[]>([]);

  // Update candles when new candle arrives
  useEffect(() => {
    if (latestCandle) {
      setCandles((prev) => {
        const newCandles = [...prev, latestCandle];
        return newCandles.slice(-100); // Keep last 100 candles
      });
    }
  }, [latestCandle]);

  // Update equity data when new portfolio snapshot arrives
  useEffect(() => {
    if (portfolio) {
      setEquityData((prev) => {
        const newData = [...prev, portfolio];
        return newData.slice(-50); // Keep last 50 snapshots
      });
    }
  }, [portfolio]);

  // Show error if WebSocket fails
  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600">WebSocket Error</h2>
          <p className="mt-2 text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
      <TopBar
        connected={connected}
        portfolio={portfolio}
        selectedBot={selectedBot}
        onBotChange={setSelectedBot}
      />

      {/* Main Content */}
      <div className="mx-auto max-w-7xl p-6">
        {/* Main Panel: Equity Curve + Candlestick Chart */}
        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Equity Curve (D3) */}
          <div className="rounded-lg border bg-white p-6">
            <h3 className="mb-4 text-lg font-semibold">Equity Curve</h3>
            {equityData.length > 0 ? (
              <EquityCurveChart data={equityData} width={600} height={300} />
            ) : (
              <div className="flex h-80 items-center justify-center text-gray-500">
                Waiting for portfolio data...
              </div>
            )}
          </div>

          {/* Candlestick Chart (recharts) */}
          <CandlestickChart candles={candles} patterns={patterns} />
        </div>

        {/* Bottom Panel: Positions, Risk, Orders */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <OpenPositions positions={openPositions} />
          <RiskMeters riskStatus={riskStatus} />
          <RecentOrders orders={recentOrders} />
        </div>
      </div>
    </div>
  );
}
