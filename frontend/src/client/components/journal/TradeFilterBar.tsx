/**
 * TradeFilterBar - Filters for trade journal
 * AUT-356
 */
import { useState } from 'react';

interface TradeFilterBarProps {
  onFilterChange: (filters: {
    bot_id?: string;
    direction?: 'LONG' | 'SHORT' | 'ALL';
    start_date?: string;
    end_date?: string;
  }) => void;
}

export function TradeFilterBar({ onFilterChange }: TradeFilterBarProps) {
  const [botId, setBotId] = useState<string>('');
  const [direction, setDirection] = useState<'LONG' | 'SHORT' | 'ALL'>('ALL');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  const handleApplyFilters = () => {
    onFilterChange({
      bot_id: botId || undefined,
      direction: direction !== 'ALL' ? direction : undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow mb-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Bot ID
          </label>
          <input
            type="text"
            value={botId}
            onChange={(e) => setBotId(e.target.value)}
            placeholder="All bots"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Direction
          </label>
          <select
            value={direction}
            onChange={(e) => setDirection(e.target.value as 'LONG' | 'SHORT' | 'ALL')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option value="ALL">All</option>
            <option value="LONG">Long</option>
            <option value="SHORT">Short</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>
      </div>

      <div className="mt-4">
        <button
          onClick={handleApplyFilters}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium"
        >
          Apply Filters
        </button>
      </div>
    </div>
  );
}
