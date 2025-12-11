import React, { useState, useEffect } from "react";
import { apiClient, ApiClient } from "@/services/api";
import type { CoverageHeatMapResponse, CoverageDateRow, SymbolsList } from "@/types/etl";
import { TIMEFRAMES } from "@/types/etl";
import {
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Filter
} from "lucide-react";

type StatusFilter = 'all' | 'complete' | 'partial' | 'missing';

export const CoverageHeatMap: React.FC = () => {
  const [data, setData] = useState<CoverageHeatMapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [symbols, setSymbols] = useState<string[]>([]);

  // Fetch symbols on mount
  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const response = await fetch("/api/v1/etl/symbols/list");
        if (response.ok) {
          const data: SymbolsList = await response.json();
          setSymbols(data.symbols);
        }
      } catch (err) {
        console.error("Error fetching symbols:", err);
      }
    };
    fetchSymbols();
  }, []);

  const fetchCoverage = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getCoverageHeatmap(
        selectedSymbol || undefined
      );
      setData(response);
    } catch (err) {
      setError(ApiClient.getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoverage();
  }, [selectedSymbol]);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'complete':
        return 'bg-green-500 dark:bg-green-600';
      case 'partial':
        return 'bg-yellow-500 dark:bg-yellow-600';
      case 'missing':
        return 'bg-red-500 dark:bg-red-600';
      default:
        return 'bg-gray-300 dark:bg-gray-700';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle2 className="h-3 w-3" />;
      case 'partial':
        return <AlertTriangle className="h-3 w-3" />;
      case 'missing':
        return <XCircle className="h-3 w-3" />;
      default:
        return null;
    }
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr + 'T00:00:00');
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const dayOfWeek = dayNames[date.getDay()];
    const formatted = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
    return `${dayOfWeek} ${formatted}`;
  };

  // Filter coverage matrix by status
  const filteredMatrix = data?.coverage_matrix.filter(row => {
    if (statusFilter === 'all') return true;

    // Check if any timeframe in this row matches the filter
    return Object.values(row.timeframes).some(cell => cell.status === statusFilter);
  }) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8" data-testid="coverage-heatmap-loading">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading coverage data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg" data-testid="coverage-heatmap-error">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button
          onClick={fetchCoverage}
          className="mt-2 px-4 py-2 bg-red-100 dark:bg-red-900/30 rounded hover:bg-red-200 dark:hover:bg-red-900/50 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-4 text-center text-muted-foreground" data-testid="coverage-heatmap-empty">
        No coverage data available
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="coverage-heatmap">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm">
            <CheckCircle2 className="h-4 w-4" />
            Complete
          </div>
          <div className="text-2xl font-bold mt-1 text-green-700 dark:text-green-300" data-testid="summary-complete">
            {data.summary.complete}
          </div>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400 text-sm">
            <AlertTriangle className="h-4 w-4" />
            Partial
          </div>
          <div className="text-2xl font-bold mt-1 text-yellow-700 dark:text-yellow-300" data-testid="summary-partial">
            {data.summary.partial}
          </div>
        </div>
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
            <XCircle className="h-4 w-4" />
            Missing
          </div>
          <div className="text-2xl font-bold mt-1 text-red-700 dark:text-red-300" data-testid="summary-missing">
            {data.summary.missing}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Filter:</span>
        </div>

        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="px-3 py-1.5 bg-background border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          data-testid="symbol-filter"
        >
          <option value="">All Symbols</option>
          {symbols.map(sym => (
            <option key={sym} value={sym}>{sym}</option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          className="px-3 py-1.5 bg-background border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          data-testid="status-filter"
        >
          <option value="all">All Status</option>
          <option value="complete">Complete Only</option>
          <option value="partial">Partial Only</option>
          <option value="missing">Missing Only</option>
        </select>

        <button
          onClick={fetchCoverage}
          className="p-2 bg-secondary rounded-lg hover:bg-secondary/80 transition-colors ml-auto"
          title="Refresh"
          data-testid="refresh-button"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Heatmap Grid */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="coverage-table">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium sticky left-0 bg-muted/50 z-10">
                  Date
                </th>
                {TIMEFRAMES.map(tf => (
                  <th key={tf} className="px-2 py-3 text-center text-sm font-medium whitespace-nowrap">
                    {tf}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredMatrix.length === 0 ? (
                <tr>
                  <td colSpan={TIMEFRAMES.length + 1} className="px-4 py-8 text-center text-muted-foreground">
                    {statusFilter !== 'all'
                      ? `No dates with ${statusFilter} status`
                      : 'No coverage data available'}
                  </td>
                </tr>
              ) : (
                filteredMatrix.map((row) => (
                  <tr
                    key={row.date}
                    className="hover:bg-muted/30 transition-colors"
                    data-testid={`coverage-row-${row.date}`}
                  >
                    <td className="px-4 py-2 text-sm font-medium sticky left-0 bg-background z-10">
                      {formatDate(row.date)}
                    </td>
                    {TIMEFRAMES.map(tf => {
                      const cell = row.timeframes[tf];
                      if (!cell) {
                        return (
                          <td key={tf} className="px-2 py-2 text-center">
                            <div className="w-8 h-8 mx-auto bg-gray-100 dark:bg-gray-800 rounded" />
                          </td>
                        );
                      }

                      return (
                        <td key={tf} className="px-2 py-2 text-center">
                          <div
                            className={`w-8 h-8 mx-auto rounded flex items-center justify-center text-white cursor-help ${getStatusColor(cell.status)}`}
                            title={`${cell.candles}${cell.expected ? `/${cell.expected}` : ''} candles`}
                            data-testid={`cell-${row.date}-${tf}`}
                          >
                            {cell.candles > 0 && (
                              <span className="text-xs font-medium">
                                {cell.candles >= 1000 ? `${Math.round(cell.candles / 100) / 10}k` : cell.candles}
                              </span>
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-500" />
          <span>Complete</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-yellow-500" />
          <span>Partial</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-500" />
          <span>Missing</span>
        </div>
      </div>

      {/* Date range info */}
      {data.date_range && (
        <div className="text-sm text-muted-foreground text-center">
          Coverage from {formatDate(data.date_range.start)} to {formatDate(data.date_range.end)}
          {data.symbol && ` for ${data.symbol}`}
        </div>
      )}
    </div>
  );
};
