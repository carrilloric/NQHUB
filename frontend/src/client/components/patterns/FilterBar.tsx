import { useState } from 'react';
import type { DateRange } from '@/hooks/usePatterns';

export interface FilterBarProps {
  timeframe: string;
  onTimeframeChange: (timeframe: string) => void;
  status: string;
  onStatusChange: (status: string) => void;
  dateRange?: DateRange;
  onDateRangeChange?: (dateRange: DateRange) => void;
}

const TIMEFRAMES = ['1min', '5min', '15min', '1h', '4h'];
const STATUSES = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'mitigated', label: 'Mitigated' },
  { value: 'broken', label: 'Broken' },
];

export function FilterBar({
  timeframe,
  onTimeframeChange,
  status,
  onStatusChange,
  dateRange,
  onDateRangeChange,
}: FilterBarProps) {
  const [localStartDate, setLocalStartDate] = useState(dateRange?.start || '');
  const [localEndDate, setLocalEndDate] = useState(dateRange?.end || '');

  const handleDateRangeApply = () => {
    if (onDateRangeChange && localStartDate && localEndDate) {
      onDateRangeChange({
        start: localStartDate,
        end: localEndDate,
      });
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Timeframe Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Timeframe
          </label>
          <select
            value={timeframe}
            onChange={(e) => onTimeframeChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {TIMEFRAMES.map((tf) => (
              <option key={tf} value={tf}>
                {tf}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            value={status}
            onChange={(e) => onStatusChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range Picker */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Date Range
          </label>
          <div className="flex space-x-2">
            <input
              type="date"
              value={localStartDate}
              onChange={(e) => setLocalStartDate(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="date"
              value={localEndDate}
              onChange={(e) => setLocalEndDate(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleDateRangeApply}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}