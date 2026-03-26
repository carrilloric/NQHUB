import React, { createContext, useContext, useCallback, useEffect, useState, useRef } from "react";
import { apiClient } from "@/services/api";

interface ServerTimeData {
  utc: Date;              // UTC time
  et: Date;               // Eastern Time
  etNaive: string;        // ET string for display (e.g., "2024-11-29 14:30:45")
  timezone: string;       // Timezone setting (e.g., "America/New_York")
  offsetHours: number;    // Current offset from UTC
  isDst: boolean;         // DST status
  localOffset: number;    // Client-server time offset in milliseconds
}

interface ServerTimeContextType {
  // Current server time (auto-updated)
  serverTime: ServerTimeData | null;

  // Get current server time (calculated from last sync + elapsed time)
  getCurrentTime: () => ServerTimeData | null;

  // Get formatted time strings
  getFormattedET: () => string;  // Returns "YYYY-MM-DD HH:MM:SS ET"
  getFormattedUTC: () => string; // Returns "YYYY-MM-DD HH:MM:SS UTC"

  // Manual sync
  syncTime: () => Promise<void>;

  // Connection status
  isConnected: boolean;
  lastSyncTime: Date | null;
  syncError: string | null;
}

const ServerTimeContext = createContext<ServerTimeContextType | null>(null);

// Sync interval in milliseconds
const SYNC_INTERVAL = 60000; // 60 seconds
const HEARTBEAT_INTERVAL = 5000; // 5 seconds for quick checks

export const ServerTimeProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [serverTime, setServerTime] = useState<ServerTimeData | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  // Refs for accurate time tracking
  const lastSyncRef = useRef<number>(0);
  const localOffsetRef = useRef<number>(0);
  const intervalRef = useRef<NodeJS.Timeout>();
  const heartbeatRef = useRef<NodeJS.Timeout>();

  // Parse server response
  const parseServerTime = useCallback((data: any): ServerTimeData => {
    const serverUtc = new Date(data.utc);
    const serverEt = new Date(data.et);
    const clientNow = Date.now();

    // Calculate offset between client and server
    const offset = serverUtc.getTime() - clientNow;

    return {
      utc: serverUtc,
      et: serverEt,
      etNaive: data.et_naive,
      timezone: data.timezone,
      offsetHours: data.offset_hours,
      isDst: data.is_dst,
      localOffset: offset
    };
  }, []);

  // Sync time with server
  const syncTime = useCallback(async () => {
    try {
      const data = await apiClient.get('/system/time');
      const timeData = parseServerTime(data);

      setServerTime(timeData);
      setLastSyncTime(new Date());
      lastSyncRef.current = Date.now();
      localOffsetRef.current = timeData.localOffset;
      setIsConnected(true);
      setSyncError(null);
    } catch (error) {
      console.error('Failed to sync server time:', error);
      setSyncError('Failed to sync with server');
      setIsConnected(false);
    }
  }, [parseServerTime]);

  // Get current time (calculated from last sync + elapsed time)
  const getCurrentTime = useCallback((): ServerTimeData | null => {
    if (!serverTime || !lastSyncRef.current) return null;

    // Calculate elapsed time since last sync
    const elapsed = Date.now() - lastSyncRef.current;

    // Update times based on elapsed time
    const currentUtc = new Date(serverTime.utc.getTime() + elapsed);
    const currentEt = new Date(serverTime.et.getTime() + elapsed);

    // Format ET time string
    const etNaive = currentEt.toISOString()
      .replace('T', ' ')
      .replace(/\.\d{3}Z$/, '')
      .substring(0, 19);

    return {
      ...serverTime,
      utc: currentUtc,
      et: currentEt,
      etNaive
    };
  }, [serverTime]);

  // Get formatted Eastern Time
  const getFormattedET = useCallback((): string => {
    const current = getCurrentTime();
    if (!current) return 'Loading...';

    const etTime = current.etNaive;
    const utcTime = current.utc.toISOString().replace('T', ' ').substring(0, 19);

    // Return format: "2024-11-29 14:30:45 ET (19:30:45 UTC)"
    return `${etTime} ET (${utcTime} UTC)`;
  }, [getCurrentTime]);

  // Get formatted UTC time
  const getFormattedUTC = useCallback((): string => {
    const current = getCurrentTime();
    if (!current) return 'Loading...';

    return current.utc.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  }, [getCurrentTime]);

  // Heartbeat check (lightweight)
  const heartbeatCheck = useCallback(async () => {
    try {
      const data = await apiClient.get('/system/heartbeat');
      if (data && data.status === 'ok') {
        setIsConnected(true);
      }
    } catch (error) {
      console.warn('Heartbeat check failed');
      setIsConnected(false);
    }
  }, []);

  // Initial sync on mount
  useEffect(() => {
    syncTime();

    // Set up sync interval
    intervalRef.current = setInterval(syncTime, SYNC_INTERVAL);

    // Set up heartbeat interval
    heartbeatRef.current = setInterval(heartbeatCheck, HEARTBEAT_INTERVAL);

    // Sync on visibility change (when tab becomes active)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        syncTime();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [syncTime, heartbeatCheck]);

  const contextValue: ServerTimeContextType = {
    serverTime,
    getCurrentTime,
    getFormattedET,
    getFormattedUTC,
    syncTime,
    isConnected,
    lastSyncTime,
    syncError
  };

  return (
    <ServerTimeContext.Provider value={contextValue}>
      {children}
    </ServerTimeContext.Provider>
  );
};

// Hook to use server time
export const useServerTime = () => {
  const context = useContext(ServerTimeContext);
  if (!context) {
    throw new Error("useServerTime must be used within ServerTimeProvider");
  }
  return context;
};

// Utility function to convert any date to ET format
export const formatToET = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;

  // This is a simplified version - in production you'd want to use
  // the server's timezone configuration for accuracy
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  };

  const parts = new Intl.DateTimeFormat('en-US', options).formatToParts(d);
  const formatted: any = {};

  parts.forEach(part => {
    formatted[part.type] = part.value;
  });

  return `${formatted.year}-${formatted.month}-${formatted.day} ${formatted.hour}:${formatted.minute}:${formatted.second} ET`;
};