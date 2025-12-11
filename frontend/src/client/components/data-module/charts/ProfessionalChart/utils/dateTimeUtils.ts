/**
 * Date and Time utility functions for chart operations
 */

export function formatDateTime(date: Date): string {
  return date.toISOString();
}

export function formatDateForDisplay(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
}

export function formatTimeForDisplay(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

export function getTimeframeInterval(timeframe: string): number {
  const intervals: Record<string, number> = {
    '30s': 30 * 1000,
    '1m': 60 * 1000,
    '5m': 5 * 60 * 1000,
    '15m': 15 * 60 * 1000,
    '1h': 60 * 60 * 1000,
    '4h': 4 * 60 * 60 * 1000,
    '1d': 24 * 60 * 60 * 1000,
    '1w': 7 * 24 * 60 * 60 * 1000,
  };

  return intervals[timeframe] || intervals['5m'];
}

export function calculateEndDate(startDate: Date, barCount: number, timeframe: string): Date {
  const interval = getTimeframeInterval(timeframe);
  return new Date(startDate.getTime() + barCount * interval);
}

export function isWithinRange(date: Date, start: Date, end: Date): boolean {
  const time = date.getTime();
  return time >= start.getTime() && time <= end.getTime();
}

export function parseAPIDateTime(dateString: string): Date {
  return new Date(dateString);
}

export function formatForAPI(date: Date): string {
  return date.toISOString();
}
