/**
 * Connection Status Component
 *
 * Displays WebSocket connection status with bot information
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import {
  WifiIcon,
  WifiOffIcon,
  RefreshCwIcon,
  AlertTriangleIcon,
  BotIcon,
  PlayIcon,
  TrendingUpIcon
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  botName?: string;
  mode?: 'paper' | 'live';
}

export default function ConnectionStatus({ status, botName = 'NQ Bot', mode = 'paper' }: ConnectionStatusProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'connected':
        return <WifiIcon className="w-4 h-4 text-green-600" />;
      case 'connecting':
        return <RefreshCwIcon className="w-4 h-4 text-yellow-600 animate-spin" />;
      case 'disconnected':
        return <WifiOffIcon className="w-4 h-4 text-gray-500" />;
      case 'error':
        return <AlertTriangleIcon className="w-4 h-4 text-red-600" />;
      default:
        return <WifiOffIcon className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Connection Error';
      default:
        return 'Unknown';
    }
  };

  const getStatusClass = () => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-400';
      case 'connecting':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-400';
      case 'disconnected':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  return (
    <div className="flex items-center gap-3">
      {/* Connection Status Badge */}
      <Badge
        variant="outline"
        className={cn(
          "flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium transition-all",
          getStatusClass()
        )}
      >
        {getStatusIcon()}
        <span>{getStatusText()}</span>
      </Badge>

      {/* Bot Name */}
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <BotIcon className="w-4 h-4" />
        <span className="font-medium">{botName}</span>
      </div>

      {/* Trading Mode Badge */}
      <Badge
        variant={mode === 'live' ? 'destructive' : 'secondary'}
        className={cn(
          "text-xs font-medium uppercase",
          mode === 'live'
            ? 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800'
            : 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-400'
        )}
      >
        {mode === 'live' ? (
          <TrendingUpIcon className="w-3 h-3 mr-1" />
        ) : (
          <PlayIcon className="w-3 h-3 mr-1" />
        )}
        {mode}
      </Badge>

      {/* Connection Indicator Dot */}
      {status === 'connected' && (
        <div className="relative">
          <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></div>
          <div className="absolute inset-0 w-2 h-2 bg-green-600 rounded-full animate-ping"></div>
        </div>
      )}
    </div>
  );
}