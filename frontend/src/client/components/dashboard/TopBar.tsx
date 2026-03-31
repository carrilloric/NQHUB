/**
 * TopBar Component
 *
 * Displays:
 * - Bot selector dropdown
 * - WebSocket connection status
 * - Global P&L for the day
 */
import { useState } from 'react';
import type { PortfolioSnapshot } from '@/stores/websocketStore';

interface TopBarProps {
  connected: boolean;
  portfolio: PortfolioSnapshot | null;
  selectedBot?: string;
  onBotChange?: (botId: string) => void;
}

export function TopBar({ connected, portfolio, selectedBot, onBotChange }: TopBarProps) {
  const [activeBotId] = useState(selectedBot || 'bot-1');

  // Calculate daily P&L
  const dailyPnL = portfolio?.daily_pnl ?? 0;
  const pnlColor = dailyPnL >= 0 ? 'text-green-600' : 'text-red-600';

  return (
    <div className="flex items-center justify-between px-6 py-4 bg-white border-b">
      {/* Left: Bot Selector */}
      <div className="flex items-center gap-4">
        <label htmlFor="bot-select" className="text-sm font-medium text-gray-700">
          Active Bot:
        </label>
        <select
          id="bot-select"
          value={activeBotId}
          onChange={(e) => onBotChange?.(e.target.value)}
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        >
          <option value="bot-1">Bot 1 - NQ Scalper</option>
          <option value="bot-2">Bot 2 - Swing Trader</option>
          <option value="bot-3">Bot 3 - Grid Bot</option>
        </select>
      </div>

      {/* Center: Connection Status */}
      <div className="flex items-center gap-2">
        <div
          className={`h-3 w-3 rounded-full ${
            connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`}
          data-testid="connection-indicator"
        />
        <span className="text-sm font-medium text-gray-700">
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Right: Global P&L */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-700">Daily P&L:</span>
        <span className={`text-lg font-bold ${pnlColor}`} data-testid="daily-pnl">
          ${dailyPnL.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
