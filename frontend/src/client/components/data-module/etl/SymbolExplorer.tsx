import React, { useState, useEffect, useMemo } from "react";
import { apiClient, ApiClient } from "@/services/api";
import type { SymbolDetail, SymbolDetailsList } from "@/types/etl";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  RefreshCw,
  Database,
  Calendar,
  Activity
} from "lucide-react";

type SortField = 'symbol' | 'total_ticks' | 'total_candles' | 'days_covered' | 'avg_ticks_per_day' | 'first_tick' | 'last_tick';
type SortDirection = 'asc' | 'desc';

export const SymbolExplorer: React.FC = () => {
  const [symbols, setSymbols] = useState<SymbolDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<SortField>('total_ticks');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const fetchSymbols = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getSymbolDetails();
      setSymbols(data.symbols);
    } catch (err) {
      setError(ApiClient.getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSymbols();
  }, []);

  // Filter and sort symbols
  const filteredAndSortedSymbols = useMemo(() => {
    let result = [...symbols];

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(s => s.symbol.toLowerCase().includes(term));
    }

    // Sort
    result.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      // Handle null values
      if (aVal === null) aVal = sortDirection === 'asc' ? Infinity : -Infinity;
      if (bVal === null) bVal = sortDirection === 'asc' ? Infinity : -Infinity;

      // Compare
      if (typeof aVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return result;
  }, [symbols, searchTerm, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 ml-1 opacity-50" />;
    }
    return sortDirection === 'asc'
      ? <ArrowUp className="h-4 w-4 ml-1" />
      : <ArrowDown className="h-4 w-4 ml-1" />;
  };

  const formatNumber = (num: number): string => {
    if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`;
    }
    if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`;
    }
    return num.toLocaleString();
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Calculate totals
  const totals = useMemo(() => {
    return {
      ticks: symbols.reduce((sum, s) => sum + s.total_ticks, 0),
      candles: symbols.reduce((sum, s) => sum + s.total_candles, 0),
      symbols: symbols.length
    };
  }, [symbols]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8" data-testid="symbol-explorer-loading">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading symbols...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg" data-testid="symbol-explorer-error">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button
          onClick={fetchSymbols}
          className="mt-2 px-4 py-2 bg-red-100 dark:bg-red-900/30 rounded hover:bg-red-200 dark:hover:bg-red-900/50 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="symbol-explorer">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Database className="h-4 w-4" />
            Total Ticks
          </div>
          <div className="text-2xl font-bold mt-1" data-testid="total-ticks">
            {formatNumber(totals.ticks)}
          </div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Activity className="h-4 w-4" />
            Total Candles
          </div>
          <div className="text-2xl font-bold mt-1" data-testid="total-candles">
            {formatNumber(totals.candles)}
          </div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Calendar className="h-4 w-4" />
            Symbols
          </div>
          <div className="text-2xl font-bold mt-1" data-testid="total-symbols">
            {totals.symbols}
          </div>
        </div>
      </div>

      {/* Search and Refresh */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search symbols..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            data-testid="symbol-search"
          />
        </div>
        <button
          onClick={fetchSymbols}
          className="p-2 bg-secondary rounded-lg hover:bg-secondary/80 transition-colors"
          title="Refresh"
          data-testid="refresh-button"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="symbols-table">
            <thead className="bg-muted/50">
              <tr>
                <th
                  className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort('symbol')}
                >
                  <div className="flex items-center">
                    Symbol
                    <SortIcon field="symbol" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort('total_ticks')}
                >
                  <div className="flex items-center justify-end">
                    Ticks
                    <SortIcon field="total_ticks" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort('total_candles')}
                >
                  <div className="flex items-center justify-end">
                    Candles
                    <SortIcon field="total_candles" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort('days_covered')}
                >
                  <div className="flex items-center justify-end">
                    Days
                    <SortIcon field="days_covered" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort('avg_ticks_per_day')}
                >
                  <div className="flex items-center justify-end">
                    Avg/Day
                    <SortIcon field="avg_ticks_per_day" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort('first_tick')}
                >
                  <div className="flex items-center">
                    First Tick
                    <SortIcon field="first_tick" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort('last_tick')}
                >
                  <div className="flex items-center">
                    Last Tick
                    <SortIcon field="last_tick" />
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">
                  Timeframes
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredAndSortedSymbols.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">
                    {searchTerm ? 'No symbols match your search' : 'No symbols found'}
                  </td>
                </tr>
              ) : (
                filteredAndSortedSymbols.map((symbol) => (
                  <tr
                    key={symbol.symbol}
                    className="hover:bg-muted/30 transition-colors"
                    data-testid={`symbol-row-${symbol.symbol}`}
                  >
                    <td className="px-4 py-3 font-mono font-medium">
                      {symbol.symbol}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {formatNumber(symbol.total_ticks)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {formatNumber(symbol.total_candles)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {symbol.days_covered}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {formatNumber(symbol.avg_ticks_per_day)}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(symbol.first_tick)}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(symbol.last_tick)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {symbol.timeframes_available.length > 0 ? (
                          symbol.timeframes_available.map(tf => (
                            <span
                              key={tf}
                              className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded"
                            >
                              {tf}
                            </span>
                          ))
                        ) : (
                          <span className="text-muted-foreground text-xs">None</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer info */}
      <div className="text-sm text-muted-foreground text-right">
        Showing {filteredAndSortedSymbols.length} of {symbols.length} symbols
      </div>
    </div>
  );
};
