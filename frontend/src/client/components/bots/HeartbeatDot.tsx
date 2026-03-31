/**
 * HeartbeatDot Component (AUT-354)
 *
 * Displays a pulsing dot indicator that animates ONLY when bot status is RUNNING.
 * Uses CSS pulse animation for smooth visual feedback.
 */

import React from 'react';
import { cn } from '@/lib/utils';
import type { BotStatus } from './StatusBadge';

interface HeartbeatDotProps {
  status: BotStatus;
  className?: string;
}

export function HeartbeatDot({ status, className }: HeartbeatDotProps) {
  const isRunning = status === 'RUNNING';

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      {/* Outer pulse ring - only animates when RUNNING */}
      {isRunning && (
        <span
          className="absolute inline-flex h-full w-full rounded-full bg-[#22c55e] opacity-75 animate-ping"
          style={{ animationDuration: '1.5s' }}
        />
      )}

      {/* Inner dot - always visible, color matches status */}
      <span
        className={cn(
          'relative inline-flex rounded-full h-3 w-3',
          isRunning ? 'bg-[#22c55e]' : 'bg-[#6b7280]'
        )}
      />
    </div>
  );
}
