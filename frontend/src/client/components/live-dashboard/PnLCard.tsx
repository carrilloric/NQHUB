/**
 * P&L Card Component
 *
 * Displays real-time profit & loss metrics
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpIcon, ArrowDownIcon, TrendingUp, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PnLCardProps {
  balance: number;
  equity: number;
  unrealizedPnL: number;
  realizedPnLToday: number;
  dailyTrades: number;
  winRate: number;
  maxDrawdown: number;
}

export default function PnLCard({
  balance,
  equity,
  unrealizedPnL,
  realizedPnLToday,
  dailyTrades,
  winRate,
  maxDrawdown
}: PnLCardProps) {
  const totalPnL = unrealizedPnL + realizedPnLToday;
  const isPositive = totalPnL >= 0;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Profit & Loss
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Balance</p>
            <p className="text-2xl font-bold">{formatCurrency(balance)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Equity</p>
            <p className="text-2xl font-bold">{formatCurrency(equity)}</p>
          </div>
        </div>

        {/* P&L Metrics */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Unrealized P&L</span>
            <span className={cn(
              "font-medium flex items-center gap-1",
              unrealizedPnL >= 0 ? "text-green-600" : "text-red-600"
            )}>
              {unrealizedPnL >= 0 ? (
                <ArrowUpIcon className="w-4 h-4" />
              ) : (
                <ArrowDownIcon className="w-4 h-4" />
              )}
              {formatCurrency(Math.abs(unrealizedPnL))}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Realized Today</span>
            <span className={cn(
              "font-medium flex items-center gap-1",
              realizedPnLToday >= 0 ? "text-green-600" : "text-red-600"
            )}>
              {realizedPnLToday >= 0 ? (
                <ArrowUpIcon className="w-4 h-4" />
              ) : (
                <ArrowDownIcon className="w-4 h-4" />
              )}
              {formatCurrency(Math.abs(realizedPnLToday))}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Total P&L</span>
            <span className={cn(
              "font-bold text-lg flex items-center gap-1",
              isPositive ? "text-green-600" : "text-red-600"
            )}>
              {isPositive ? (
                <ArrowUpIcon className="w-4 h-4" />
              ) : (
                <ArrowDownIcon className="w-4 h-4" />
              )}
              {formatCurrency(Math.abs(totalPnL))}
            </span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 pt-4 border-t text-center">
          <div>
            <p className="text-xs text-muted-foreground">Win Rate</p>
            <p className={cn(
              "text-sm font-medium",
              winRate >= 0.5 ? "text-green-600" : "text-red-600"
            )}>
              {formatPercent(winRate)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Trades</p>
            <p className="text-sm font-medium">{dailyTrades}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Max DD</p>
            <p className="text-sm font-medium text-red-600">
              {formatCurrency(maxDrawdown)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}