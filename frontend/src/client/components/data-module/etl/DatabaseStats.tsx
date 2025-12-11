import React, { useState, useEffect } from "react";
import {
  Database,
  Calendar,
  Hash,
  Activity,
  RefreshCw,
  TrendingUp,
  BarChart3,
  Loader,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { apiClient } from "@/services/api";
import { type DatabaseStatistics, TIMEFRAMES } from "@/types/etl";
import { cn } from "@/lib/utils";

export const DatabaseStats: React.FC = () => {
  const [stats, setStats] = useState<DatabaseStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      setError(null);
      const data = await apiClient.getDatabaseStatistics();
      setStats(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load statistics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  const formatNumber = (num: number): string => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
    return num.toString();
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateDateRange = (start: string, end: string): string => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return '1 día';
    if (diffDays < 30) return `${diffDays} días`;
    if (diffDays < 365) return `${Math.round(diffDays / 30)} meses`;
    return `${Math.round(diffDays / 365 * 10) / 10} años`;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader className="size-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-4">
            <AlertCircle className="size-8 text-red-500" />
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button onClick={handleRefresh} size="sm" variant="outline">
              <RefreshCw className="size-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) return null;

  const totalCandles = Object.values(stats.candles_by_timeframe).reduce((sum, count) => sum + count, 0);
  const maxCandles = Math.max(...Object.values(stats.candles_by_timeframe), 1);

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="size-5 text-primary" />
          <h3 className="text-lg font-semibold">Database Statistics</h3>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw className={cn("size-4 mr-2", refreshing && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Ticks */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Ticks</p>
                <p className="text-2xl font-bold">{formatNumber(stats.total_ticks)}</p>
              </div>
              <Activity className="size-8 text-blue-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        {/* Date Range */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Data Range</p>
                {stats.date_range ? (
                  <div>
                    <p className="text-lg font-semibold">
                      {calculateDateRange(stats.date_range.min, stats.date_range.max)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(stats.date_range.min)} - {formatDate(stats.date_range.max)}
                    </p>
                  </div>
                ) : (
                  <p className="text-lg text-muted-foreground">No data</p>
                )}
              </div>
              <Calendar className="size-8 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        {/* Unique Symbols */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Symbols</p>
                <p className="text-2xl font-bold">{stats.unique_symbols}</p>
                <p className="text-xs text-muted-foreground">
                  {stats.spread_ticks > 0 && `${formatNumber(stats.spread_ticks)} spreads`}
                </p>
              </div>
              <Hash className="size-8 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        {/* Total Candles */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Candles</p>
                <p className="text-2xl font-bold">{formatNumber(totalCandles)}</p>
                <p className="text-xs text-muted-foreground">
                  {Object.keys(stats.candles_by_timeframe).length} timeframes
                </p>
              </div>
              <BarChart3 className="size-8 text-orange-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Candles by Timeframe */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Candles by Timeframe</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {TIMEFRAMES.map((timeframe) => {
              const count = stats.candles_by_timeframe[timeframe] || 0;
              const percentage = maxCandles > 0 ? (count / maxCandles) * 100 : 0;

              return (
                <div key={timeframe} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{timeframe}</span>
                    <span className="text-muted-foreground">{formatNumber(count)}</span>
                  </div>
                  <Progress value={percentage} className="h-2" />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Additional Info */}
      {stats.rollover_count > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="size-4 text-primary" />
                <span className="text-sm">Rollover Periods Detected</span>
              </div>
              <Badge variant="outline">{stats.rollover_count}</Badge>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};