/**
 * BotCard Component (AUT-354)
 *
 * Main bot display card integrating all bot management components:
 * - StatusBadge with HeartbeatDot
 * - Metrics summary (daily P&L, open contracts)
 * - ActionButtons (Start/Stop/Kill)
 * - StateLogTimeline (collapsible)
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { StatusBadge, type BotStatus } from './StatusBadge';
import { HeartbeatDot } from './HeartbeatDot';
import { ActionButtons } from './ActionButtons';
import { StateLogTimeline } from './StateLogTimeline';
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

interface BotCardProps {
  bot: {
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
  };
  stateLog: Array<{
    from: BotStatus;
    to: BotStatus;
    reason: string;
    timestamp: string;
  }>;
  onStart: (botId: string) => void;
  onStop: (botId: string) => void;
  onKill: (botId: string) => void;
  isLoading?: boolean;
}

export function BotCard({
  bot,
  stateLog,
  onStart,
  onStop,
  onKill,
  isLoading = false,
}: BotCardProps) {
  const [showStateLog, setShowStateLog] = useState(false);

  const isPnlPositive = bot.daily_pnl >= 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          {/* Bot name and status */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold">{bot.name}</h3>
              <HeartbeatDot status={bot.status} />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={bot.status} />
              <Badge variant="outline" className="text-xs">
                {bot.mode === 'live' ? '🔴 LIVE' : '📝 PAPER'}
              </Badge>
              {bot.apex_account_id && (
                <Badge variant="secondary" className="text-xs">
                  Apex: {bot.apex_account_id.slice(0, 8)}...
                </Badge>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <ActionButtons
            botId={bot.id}
            status={bot.status}
            onStart={onStart}
            onStop={onStop}
            onKill={onKill}
            isLoading={isLoading}
          />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Metrics Summary */}
        <div className="grid grid-cols-3 gap-4">
          {/* Daily P&L */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Daily P&L</p>
            <div className="flex items-center gap-1">
              {isPnlPositive ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span
                className={cn(
                  'text-lg font-semibold',
                  isPnlPositive ? 'text-green-600' : 'text-red-600'
                )}
              >
                ${Math.abs(bot.daily_pnl).toFixed(2)}
              </span>
            </div>
          </div>

          {/* Open Contracts */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Open Contracts</p>
            <p className="text-lg font-semibold">{bot.open_contracts}</p>
          </div>

          {/* Last Heartbeat */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Last Heartbeat</p>
            <p className="text-sm">
              {formatDistanceToNow(new Date(bot.last_heartbeat), {
                addSuffix: true,
              })}
            </p>
          </div>
        </div>

        {/* Active Parameters */}
        {Object.keys(bot.active_params).length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Active Parameters</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(bot.active_params).map(([key, value]) => (
                <Badge key={key} variant="outline" className="text-xs">
                  {key}: {value}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* State Log Toggle */}
        <div className="pt-2 border-t">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowStateLog(!showStateLog)}
            className="w-full justify-between"
          >
            <span className="text-sm font-medium">State History</span>
            {showStateLog ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>

          {showStateLog && (
            <div className="mt-3">
              <StateLogTimeline states={stateLog} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
