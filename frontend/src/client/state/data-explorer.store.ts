/**
 * Data Explorer Store
 *
 * Zustand store for managing Data Explorer state including
 * timeframe selection, date range, oflow toggle, and contract selection.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { format, subDays } from 'date-fns';

interface DateRange {
  start: string;
  end: string;
}

interface DataExplorerStore {
  // State
  selectedTimeframe: string;
  dateRange: DateRange;
  includeOflow: boolean;
  selectedContract: string;

  // Actions
  setSelectedTimeframe: (timeframe: string) => void;
  setDateRange: (range: DateRange) => void;
  setIncludeOflow: (include: boolean) => void;
  setSelectedContract: (contract: string) => void;
  resetFilters: () => void;
}

// Default values
const DEFAULT_TIMEFRAME = '5min';
const DEFAULT_CONTRACT = 'NQH25';
const DEFAULT_DATE_RANGE: DateRange = {
  start: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
  end: format(new Date(), 'yyyy-MM-dd'),
};

export const useDataExplorerStore = create<DataExplorerStore>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        selectedTimeframe: DEFAULT_TIMEFRAME,
        dateRange: DEFAULT_DATE_RANGE,
        includeOflow: false,
        selectedContract: DEFAULT_CONTRACT,

        // Actions
        setSelectedTimeframe: (timeframe) =>
          set((state) => ({ ...state, selectedTimeframe: timeframe })),

        setDateRange: (range) =>
          set((state) => ({ ...state, dateRange: range })),

        setIncludeOflow: (include) =>
          set((state) => ({ ...state, includeOflow: include })),

        setSelectedContract: (contract) =>
          set((state) => ({ ...state, selectedContract: contract })),

        resetFilters: () =>
          set(() => ({
            selectedTimeframe: DEFAULT_TIMEFRAME,
            dateRange: DEFAULT_DATE_RANGE,
            includeOflow: false,
            selectedContract: DEFAULT_CONTRACT,
          })),
      }),
      {
        name: 'data-explorer-storage',
        partialize: (state) => ({
          selectedTimeframe: state.selectedTimeframe,
          includeOflow: state.includeOflow,
          selectedContract: state.selectedContract,
          // Don't persist date range as it should be fresh
        }),
      }
    ),
    {
      name: 'DataExplorerStore',
    }
  )
);