/**
 * StateLogTimeline Component (AUT-354)
 *
 * Displays the last 5 state transition events for a bot.
 * Shows from → to status changes with reason and timestamp.
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge, type BotStatus } from './StatusBadge';
import { ArrowRight, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface StateLogEntry {
  from: BotStatus;
  to: BotStatus;
  reason: string;
  timestamp: string;
}

interface StateLogTimelineProps {
  states: StateLogEntry[];
  className?: string;
}

export function StateLogTimeline({ states, className }: StateLogTimelineProps) {
  // Show last 5 events, most recent first
  const recentStates = states.slice(0, 5);

  if (recentStates.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-sm font-medium">State History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No state transitions yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          State History
          <span className="ml-2 text-xs font-normal text-muted-foreground">
            (Last {recentStates.length} events)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recentStates.map((entry, index) => (
            <div
              key={index}
              className="flex items-start gap-3 pb-3 last:pb-0 border-b last:border-0"
            >
              {/* Timeline dot */}
              <div className="flex flex-col items-center">
                <div className="h-2 w-2 rounded-full bg-primary mt-2" />
                {index < recentStates.length - 1 && (
                  <div className="w-px h-full bg-border mt-1" />
                )}
              </div>

              {/* Event details */}
              <div className="flex-1 space-y-1 min-w-0">
                {/* Status transition */}
                <div className="flex items-center gap-2 flex-wrap">
                  <StatusBadge status={entry.from} className="text-xs" />
                  <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  <StatusBadge status={entry.to} className="text-xs" />
                </div>

                {/* Reason */}
                <p className="text-sm text-foreground">{entry.reason}</p>

                {/* Timestamp */}
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>
                    {formatDistanceToNow(new Date(entry.timestamp), {
                      addSuffix: true,
                    })}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
