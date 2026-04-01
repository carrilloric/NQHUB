/**
 * RiskEventFeed Component
 *
 * Displays last 5 risk events in real-time from WebSocket.
 */
import React from 'react';
import { cn } from '@/lib/utils';

interface RiskEvent {
  ts: string;
  check_name: string;
  result: 'PASSED' | 'REJECTED';
  reason?: string;
}

interface RiskEventFeedProps {
  events: RiskEvent[];
  className?: string;
}

export function RiskEventFeed({ events, className }: RiskEventFeedProps) {
  if (events.length === 0) {
    return (
      <div className={cn('text-sm text-gray-500 dark:text-gray-400', className)}>
        No recent risk events
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
        Recent Risk Events
      </h4>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {events.slice(0, 5).map((event, index) => (
          <div
            key={index}
            className={cn(
              'px-3 py-2 rounded-md text-xs',
              event.result === 'PASSED'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            )}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{event.check_name}</span>
              <span className="text-gray-500 dark:text-gray-400">
                {new Date(event.ts).toLocaleTimeString()}
              </span>
            </div>
            {event.reason && (
              <div className="mt-1 text-gray-600 dark:text-gray-300">
                {event.reason}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
