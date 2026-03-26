import React, { useEffect, useState } from 'react';
import { useServerTime } from '@/state/server-time';
import { Clock, WifiOff, AlertCircle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from '@/lib/utils';

interface ServerTimeClockProps {
  className?: string;
  showIcon?: boolean;
  format?: 'full' | 'et' | 'compact';
}

export const ServerTimeClock: React.FC<ServerTimeClockProps> = ({
  className,
  showIcon = true,
  format = 'compact'
}) => {
  const {
    getCurrentTime,
    getFormattedET,
    isConnected,
    lastSyncTime,
    syncError
  } = useServerTime();

  const [displayTime, setDisplayTime] = useState<string>('Loading...');

  useEffect(() => {
    // Update time every second
    const updateDisplay = () => {
      const current = getCurrentTime();
      if (!current) {
        setDisplayTime('Loading...');
        return;
      }

      switch (format) {
        case 'full':
          // Full format: "2024-11-29 14:30:45 ET (19:30:45 UTC)"
          setDisplayTime(getFormattedET());
          break;
        case 'et':
          // ET only: "2024-11-29 14:30:45 ET"
          setDisplayTime(current.etNaive + ' ET');
          break;
        case 'compact':
        default:
          // Compact: "14:30:45 ET"
          const time = current.etNaive.split(' ')[1];
          setDisplayTime(time + ' ET');
          break;
      }
    };

    updateDisplay();
    const interval = setInterval(updateDisplay, 1000);

    return () => clearInterval(interval);
  }, [getCurrentTime, getFormattedET, format]);

  // Determine status color and icon
  const getStatusIndicator = () => {
    if (!isConnected) {
      return {
        color: 'text-red-500',
        icon: <WifiOff className="w-3 h-3" />,
        tooltip: 'Disconnected from server'
      };
    }
    if (syncError) {
      return {
        color: 'text-yellow-500',
        icon: <AlertCircle className="w-3 h-3" />,
        tooltip: `Sync error: ${syncError}`
      };
    }
    return {
      color: 'text-green-500',
      icon: null,
      tooltip: `Connected - Last sync: ${lastSyncTime ? new Date(lastSyncTime).toLocaleTimeString() : 'Never'}`
    };
  };

  const status = getStatusIndicator();

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted/50 border border-border",
          className
        )}>
          {showIcon && (
            <div className="flex items-center gap-1">
              <Clock className={cn("w-4 h-4", isConnected ? "text-primary" : "text-muted-foreground")} />
              {status.icon && (
                <span className={status.color}>
                  {status.icon}
                </span>
              )}
            </div>
          )}
          <span className={cn(
            "text-sm font-mono",
            isConnected ? "text-foreground" : "text-muted-foreground"
          )}>
            {displayTime}
          </span>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-xs">
        <div className="space-y-1">
          <div className="font-semibold">Server Time</div>
          <div className="text-xs text-muted-foreground">
            {status.tooltip}
          </div>
          {format === 'compact' && (
            <div className="text-xs mt-2 pt-2 border-t">
              Full: {getFormattedET()}
            </div>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  );
};

// Simplified version for minimal display
export const ServerTimeCompact: React.FC<{ className?: string }> = ({ className }) => {
  const { getCurrentTime, isConnected } = useServerTime();
  const [time, setTime] = useState<string>('--:--:--');

  useEffect(() => {
    const update = () => {
      const current = getCurrentTime();
      if (current) {
        const timeStr = current.etNaive.split(' ')[1];
        setTime(timeStr);
      }
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [getCurrentTime]);

  return (
    <span className={cn(
      "font-mono text-xs",
      isConnected ? "text-muted-foreground" : "text-red-500/50",
      className
    )}>
      {time} ET
    </span>
  );
};