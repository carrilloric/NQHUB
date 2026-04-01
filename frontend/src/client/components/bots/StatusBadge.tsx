/**
 * StatusBadge Component (AUT-354)
 *
 * Displays bot status with color coding:
 * - RUNNING: #22c55e (green)
 * - HALTED: #ef4444 (red)
 * - STOPPED: #6b7280 (gray)
 * - PAUSED: #f59e0b (amber/yellow)
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type BotStatus = 'RUNNING' | 'STOPPED' | 'HALTED' | 'PAUSED';

interface StatusBadgeProps {
  status: BotStatus;
  className?: string;
}

// AUT-354 spec: exact color values
const STATUS_COLORS: Record<BotStatus, string> = {
  RUNNING: 'bg-[#22c55e] hover:bg-[#22c55e]/80', // green
  HALTED: 'bg-[#ef4444] hover:bg-[#ef4444]/80', // red
  STOPPED: 'bg-[#6b7280] hover:bg-[#6b7280]/80', // gray
  PAUSED: 'bg-[#f59e0b] hover:bg-[#f59e0b]/80', // amber/yellow
};

const STATUS_TEXT_COLORS: Record<BotStatus, string> = {
  RUNNING: 'text-white',
  HALTED: 'text-white',
  STOPPED: 'text-white',
  PAUSED: 'text-white',
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <Badge
      className={cn(
        'font-semibold',
        STATUS_COLORS[status],
        STATUS_TEXT_COLORS[status],
        className
      )}
    >
      {status}
    </Badge>
  );
}
