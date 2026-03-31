/**
 * ActionButtons Component (AUT-354)
 *
 * Bot control buttons with conditional visibility:
 * - Start: only visible when status=STOPPED
 * - Stop: only visible when status=RUNNING
 * - Kill: always visible (emergency kill switch)
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Play, Square, Skull } from 'lucide-react';
import type { BotStatus } from './StatusBadge';

interface ActionButtonsProps {
  botId: string;
  status: BotStatus;
  onStart: (botId: string) => void;
  onStop: (botId: string) => void;
  onKill: (botId: string) => void;
  isLoading?: boolean;
}

export function ActionButtons({
  botId,
  status,
  onStart,
  onStop,
  onKill,
  isLoading = false,
}: ActionButtonsProps) {
  const showStart = status === 'STOPPED';
  const showStop = status === 'RUNNING';

  return (
    <div className="flex items-center gap-2">
      {/* Start Button - only visible when STOPPED */}
      {showStart && (
        <Button
          size="sm"
          variant="default"
          onClick={() => onStart(botId)}
          disabled={isLoading}
          className="bg-[#22c55e] hover:bg-[#22c55e]/90 text-white"
        >
          <Play className="h-4 w-4 mr-1" />
          Start
        </Button>
      )}

      {/* Stop Button - only visible when RUNNING */}
      {showStop && (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onStop(botId)}
          disabled={isLoading}
        >
          <Square className="h-4 w-4 mr-1" />
          Stop
        </Button>
      )}

      {/* Kill Button - always visible */}
      <Button
        size="sm"
        variant="destructive"
        onClick={() => onKill(botId)}
        disabled={isLoading}
        className="bg-[#ef4444] hover:bg-[#ef4444]/90"
      >
        <Skull className="h-4 w-4 mr-1" />
        Kill
      </Button>
    </div>
  );
}
