import React, { useState, useEffect, useRef, useCallback } from "react";
import { Download, Loader, RefreshCw, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api";
import type { ETLJobLog, LogLevel } from "@/types/etl";
import { LOG_LEVEL_COLORS, LOG_LEVEL_BG_COLORS } from "@/types/etl";
import { cn } from "@/lib/utils";

interface JobLogViewerProps {
  jobId: string;
  autoScroll?: boolean;
  maxLines?: number;
  refreshInterval?: number; // milliseconds
}

export const JobLogViewer: React.FC<JobLogViewerProps> = ({
  jobId,
  autoScroll = true,
  maxLines = 500,
  refreshInterval = 2000, // 2 seconds
}) => {
  const [logs, setLogs] = useState<ETLJobLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [levelFilter, setLevelFilter] = useState<LogLevel | 'ALL'>('ALL');
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(autoScroll);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const result = await apiClient.getETLJobLogs(
        jobId,
        0,
        maxLines,
        levelFilter === 'ALL' ? undefined : levelFilter
      );
      // Reverse to show newest first (backend returns desc by created_at)
      setLogs(result.logs.reverse());
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  }, [jobId, maxLines, levelFilter]);

  // Initial load and polling
  useEffect(() => {
    fetchLogs();

    const interval = setInterval(() => {
      fetchLogs();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [fetchLogs, refreshInterval]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScrollEnabled && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScrollEnabled]);

  const handleRefresh = () => {
    setLoading(true);
    fetchLogs();
  };

  const handleDownload = () => {
    const logText = logs
      .map((log) => {
        const timestamp = new Date(log.created_at).toLocaleString();
        const metadata = log.metadata ? ` | ${JSON.stringify(log.metadata)}` : '';
        return `[${timestamp}] [${log.level}] ${log.message}${metadata}`;
      })
      .join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `etl-job-${jobId}-logs.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  const filteredLogCount = logs.length;

  return (
    <div className="flex flex-col h-full">
      {/* Header with controls */}
      <div className="flex flex-col gap-3 mb-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={levelFilter === 'ALL' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setLevelFilter('ALL')}
          >
            All
          </Button>
          <Button
            variant={levelFilter === 'INFO' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setLevelFilter('INFO')}
          >
            Info
          </Button>
          <Button
            variant={levelFilter === 'WARNING' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setLevelFilter('WARNING')}
          >
            Warning
          </Button>
          <Button
            variant={levelFilter === 'ERROR' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setLevelFilter('ERROR')}
          >
            Error
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {filteredLogCount} log{filteredLogCount !== 1 ? 's' : ''}
          </span>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoScrollEnabled(!autoScrollEnabled)}
            title={autoScrollEnabled ? 'Disable auto-scroll' : 'Enable auto-scroll'}
          >
            Auto-scroll: {autoScrollEnabled ? 'ON' : 'OFF'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
            title="Refresh logs"
          >
            <RefreshCw className={cn("size-4", loading && "animate-spin")} />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
            title="Download logs"
            disabled={logs.length === 0}
          >
            <Download className="size-4" />
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-3 rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Logs Container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto rounded-lg border border-border bg-black/5 dark:bg-black/20 p-3 font-mono text-xs"
      >
        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No logs found
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  "rounded px-2 py-1",
                  LOG_LEVEL_BG_COLORS[log.level]
                )}
              >
                <div className="flex items-start gap-2">
                  <span className="text-muted-foreground shrink-0">
                    [{formatTimestamp(log.created_at)}]
                  </span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "shrink-0 text-xs",
                      LOG_LEVEL_COLORS[log.level]
                    )}
                  >
                    {log.level}
                  </Badge>
                  <span className="flex-1">{log.message}</span>
                </div>
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <div className="mt-1 ml-2 text-muted-foreground">
                    {JSON.stringify(log.metadata, null, 2)}
                  </div>
                )}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>

      {/* Footer info */}
      <div className="mt-2 text-xs text-muted-foreground">
        Refreshing every {refreshInterval / 1000}s • Job ID: {jobId.substring(0, 8)}...
      </div>
    </div>
  );
};
