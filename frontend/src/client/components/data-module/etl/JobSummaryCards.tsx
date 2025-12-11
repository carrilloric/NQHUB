import React, { useState, useEffect } from "react";
import { apiClient, ApiClient } from "@/services/api";
import type { ETLJob, ETLJobList } from "@/types/etl";
import {
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Activity,
  ListTodo,
  TrendingUp
} from "lucide-react";

interface JobStats {
  total: number;
  completed: number;
  failed: number;
  active: number;
  pending: number;
  totalTicks: number;
  totalCandles: number;
  avgDuration: number; // in minutes
}

export const JobSummaryCards: React.FC = () => {
  const [stats, setStats] = useState<JobStats>({
    total: 0,
    completed: 0,
    failed: 0,
    active: 0,
    pending: 0,
    totalTicks: 0,
    totalCandles: 0,
    avgDuration: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch all jobs to calculate stats
      const data = await apiClient.listETLJobs(0, 1000);

      // Ensure jobs array exists
      const jobs = data?.jobs || [];

      // Calculate stats
      const completed = jobs.filter(j => j.status === 'completed');
      const failed = jobs.filter(j => j.status === 'failed');
      const active = jobs.filter(j =>
        ['extracting', 'parsing', 'loading_ticks', 'building_candles', 'detecting_rollovers', 'finalizing'].includes(j.status)
      );
      const pending = jobs.filter(j => j.status === 'pending');

      // Calculate total ticks and candles
      const totalTicks = jobs.reduce((sum, j) => sum + (j.ticks_inserted || 0), 0);
      const totalCandles = jobs.reduce((sum, j) => sum + (j.candles_created || 0), 0);

      // Calculate average duration for completed jobs
      let avgDuration = 0;
      if (completed.length > 0) {
        const durations = completed
          .filter(j => j.started_at && j.completed_at)
          .map(j => {
            const start = new Date(j.started_at!).getTime();
            const end = new Date(j.completed_at!).getTime();
            return (end - start) / 60000; // minutes
          });

        if (durations.length > 0) {
          avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
        }
      }

      setStats({
        total: data?.total || jobs.length,
        completed: completed.length,
        failed: failed.length,
        active: active.length,
        pending: pending.length,
        totalTicks,
        totalCandles,
        avgDuration
      });
    } catch (err) {
      console.error('JobSummaryCards fetch error:', err);
      const errorMsg = ApiClient.getErrorMessage(err);
      setError(typeof errorMsg === 'string' ? errorMsg : 'Error loading job stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();

    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatNumber = (num: number): string => {
    if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`;
    }
    if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`;
    }
    return num.toLocaleString();
  };

  const formatDuration = (minutes: number): string => {
    if (minutes < 1) {
      return '< 1 min';
    }
    if (minutes < 60) {
      return `${Math.round(minutes)} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  if (loading && stats.total === 0) {
    return (
      <div className="flex items-center justify-center p-4" data-testid="job-summary-loading">
        <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground text-sm">Loading stats...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-lg text-sm" data-testid="job-summary-error">
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div data-testid="job-summary-cards">
      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {/* Total Jobs */}
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <ListTodo className="h-4 w-4" />
            Total Jobs
          </div>
          <div className="text-2xl font-bold mt-1" data-testid="stat-total">
            {stats.total}
          </div>
        </div>

        {/* Completed */}
        <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm">
            <CheckCircle2 className="h-4 w-4" />
            Completed
          </div>
          <div className="text-2xl font-bold mt-1 text-green-700 dark:text-green-300" data-testid="stat-completed">
            {stats.completed}
          </div>
        </div>

        {/* Active */}
        <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 text-sm">
            <Activity className="h-4 w-4" />
            Active
          </div>
          <div className="text-2xl font-bold mt-1 text-blue-700 dark:text-blue-300" data-testid="stat-active">
            {stats.active}
          </div>
        </div>

        {/* Failed */}
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
            <XCircle className="h-4 w-4" />
            Failed
          </div>
          <div className="text-2xl font-bold mt-1 text-red-700 dark:text-red-300" data-testid="stat-failed">
            {stats.failed}
          </div>
        </div>
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Pending */}
        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs">
            <Clock className="h-3 w-3" />
            Pending
          </div>
          <div className="text-lg font-semibold mt-1" data-testid="stat-pending">
            {stats.pending}
          </div>
        </div>

        {/* Total Ticks */}
        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs">
            <TrendingUp className="h-3 w-3" />
            Total Ticks
          </div>
          <div className="text-lg font-semibold mt-1" data-testid="stat-ticks">
            {formatNumber(stats.totalTicks)}
          </div>
        </div>

        {/* Total Candles */}
        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs">
            <Activity className="h-3 w-3" />
            Total Candles
          </div>
          <div className="text-lg font-semibold mt-1" data-testid="stat-candles">
            {formatNumber(stats.totalCandles)}
          </div>
        </div>

        {/* Avg Duration */}
        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs">
            <Clock className="h-3 w-3" />
            Avg Duration
          </div>
          <div className="text-lg font-semibold mt-1" data-testid="stat-duration">
            {formatDuration(stats.avgDuration)}
          </div>
        </div>
      </div>
    </div>
  );
};
