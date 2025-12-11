import React, { useState, useEffect, useCallback } from "react";
import { RefreshCw, Loader, CheckCircle2, AlertCircle, Calendar, Clock, X, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/services/api";
import {
  type ETLJob,
  type JobStatus,
  STATUS_COLORS,
  STATUS_LABELS,
  isJobActive,
  isJobTerminal,
} from "@/types/etl";
import { cn } from "@/lib/utils";
import { JobLogViewer } from "./JobLogViewer";

interface JobMonitorProps {
  highlightJobId?: string | null;
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
}

export const JobMonitor: React.FC<JobMonitorProps> = ({
  highlightJobId,
  autoRefresh = true,
  refreshInterval = 2000, // 2 seconds
}) => {
  const [jobs, setJobs] = useState<ETLJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<JobStatus | 'all'>('all');
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [cancellingJobIds, setCancellingJobIds] = useState<Set<string>>(new Set());
  const [selectedJobForLogs, setSelectedJobForLogs] = useState<string | null>(null);
  const limit = 20;

  const fetchJobs = useCallback(async () => {
    try {
      const statusFilter = filterStatus === 'all' ? undefined : filterStatus;
      const result = await apiClient.listETLJobs(page * limit, limit, statusFilter);
      setJobs(result.jobs);
      setTotal(result.total);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }, [page, filterStatus, limit]);

  // Initial load
  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Auto-refresh polling
  useEffect(() => {
    if (!autoRefresh) return;

    // Check if any jobs are active
    const hasActiveJobs = jobs.some((job) => isJobActive(job.status));

    if (!hasActiveJobs) return;

    const interval = setInterval(() => {
      fetchJobs();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, jobs, refreshInterval, fetchJobs]);

  const handleRefresh = () => {
    setLoading(true);
    fetchJobs();
  };

  const handleFilterChange = (status: JobStatus | 'all') => {
    setFilterStatus(status);
    setPage(0);
  };

  const handleCancelJob = async (jobId: string) => {
    setCancellingJobIds((prev) => new Set(prev).add(jobId));
    try {
      await apiClient.cancelETLJob(jobId);
      // Refresh jobs list after successful cancellation
      await fetchJobs();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to cancel job');
    } finally {
      setCancellingJobIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(jobId);
        return newSet;
      });
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const formatDuration = (startDate: string, endDate?: string | null): string => {
    const start = new Date(startDate).getTime();
    const end = endDate ? new Date(endDate).getTime() : Date.now();
    const duration = end - start;

    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const getStatusIcon = (status: JobStatus) => {
    if (status === 'completed') return <CheckCircle2 className="size-4 text-green-600" />;
    if (status === 'failed') return <AlertCircle className="size-4 text-red-600" />;
    if (isJobActive(status)) return <Loader className="size-4 text-blue-600 animate-spin" />;
    return null;
  };

  const filteredJobs = jobs;

  return (
    <div className="space-y-4" data-testid="job-monitor">
      {/* Header with Filters and Refresh */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          <Button
            variant={filterStatus === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleFilterChange('all')}
            data-testid="filter-all"
          >
            All ({total})
          </Button>
          <Button
            variant={filterStatus === 'pending' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleFilterChange('pending')}
            data-testid="filter-pending"
          >
            Pending
          </Button>
          <Button
            variant={filterStatus === 'completed' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleFilterChange('completed')}
            data-testid="filter-completed"
          >
            Completed
          </Button>
          <Button
            variant={filterStatus === 'failed' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleFilterChange('failed')}
            data-testid="filter-failed"
          >
            Failed
          </Button>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={loading}
          data-testid="refresh-button"
        >
          <RefreshCw className={cn("size-4 mr-2", loading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Jobs List */}
      {loading && jobs.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="rounded-lg border border-border bg-accent/20 p-12 text-center">
          <p className="text-muted-foreground">No jobs found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredJobs.map((job) => (
            <div
              key={job.id}
              data-testid={`job-card-${job.id}`}
              className={cn(
                "rounded-lg border border-border bg-card p-4 transition-all",
                highlightJobId === job.id && "ring-2 ring-primary"
              )}
            >
              {/* Job Header */}
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {getStatusIcon(job.status)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{job.zip_filename}</p>
                    {job.file_size_mb && (
                      <p className="text-xs text-muted-foreground">
                        {job.file_size_mb.toFixed(2)} MB
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge
                    variant="outline"
                    className={cn(STATUS_COLORS[job.status])}
                    data-testid="job-status"
                  >
                    {STATUS_LABELS[job.status]}
                  </Badge>
                  {/* View Logs Button - Show for all jobs */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2"
                    onClick={() => setSelectedJobForLogs(job.id)}
                    title="View logs"
                  >
                    <FileText className="size-4" />
                  </Button>
                  {/* Cancel Button - Only show for pending or active jobs */}
                  {(job.status === 'pending' || isJobActive(job.status)) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => handleCancelJob(job.id)}
                      disabled={cancellingJobIds.has(job.id)}
                      title="Cancel job"
                    >
                      {cancellingJobIds.has(job.id) ? (
                        <Loader className="size-4 animate-spin" />
                      ) : (
                        <X className="size-4" />
                      )}
                    </Button>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              {(isJobActive(job.status) || job.progress_pct > 0) && (
                <div className="mb-3 space-y-2">
                  {/* Main Progress Bar */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>
                        Step {job.current_step} of {job.total_steps}
                      </span>
                      <span data-testid="job-progress">{job.progress_pct}%</span>
                    </div>
                    <Progress value={job.progress_pct} className="h-2" />
                  </div>

                  {/* Enhanced Progress Details */}
                  {(job.total_days || job.total_ticks_estimated) && (
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {/* Days Progress */}
                      {job.total_days && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Días:</span>
                          <span className="font-medium">
                            {job.days_processed}/{job.total_days}
                          </span>
                        </div>
                      )}

                      {/* Ticks Progress */}
                      {job.total_ticks_estimated && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Ticks:</span>
                          <span className="font-medium">
                            {job.ticks_inserted.toLocaleString()}/{job.total_ticks_estimated.toLocaleString()}
                          </span>
                        </div>
                      )}

                      {/* Duplicates Skipped */}
                      {job.duplicates_skipped > 0 && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Duplicados:</span>
                          <span className="font-medium text-amber-600">
                            {job.duplicates_skipped.toLocaleString()} omitidos
                          </span>
                        </div>
                      )}

                      {/* Processing Speed */}
                      {job.ticks_per_second && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Velocidad:</span>
                          <span className="font-medium">
                            {Math.round(job.ticks_per_second).toLocaleString()} ticks/s
                          </span>
                        </div>
                      )}

                      {/* Memory Usage */}
                      {job.memory_usage_mb && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Memoria:</span>
                          <span className="font-medium">
                            {job.memory_usage_mb.toFixed(0)} MB
                          </span>
                        </div>
                      )}

                      {/* Estimated Completion */}
                      {job.estimated_completion && isJobActive(job.status) && (
                        <div className="col-span-2 flex items-center justify-between">
                          <span className="text-muted-foreground">Tiempo restante:</span>
                          <span className="font-medium text-blue-600">
                            ~{formatDuration(new Date().toISOString(), job.estimated_completion)}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Job Details */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                {/* Timeframes */}
                {job.selected_timeframes && job.selected_timeframes.length > 0 && (
                  <div>
                    <p className="text-muted-foreground mb-1">Timeframes</p>
                    <p className="font-medium">{job.selected_timeframes.join(', ')}</p>
                  </div>
                )}

                {/* Statistics */}
                {(job.ticks_inserted > 0 || job.candles_created > 0) && (
                  <div>
                    <p className="text-muted-foreground mb-1">Processed</p>
                    <p className="font-medium">
                      {job.ticks_inserted > 0 && `${job.ticks_inserted.toLocaleString()} ticks`}
                      {job.ticks_inserted > 0 && job.candles_created > 0 && ' • '}
                      {job.candles_created > 0 && `${job.candles_created.toLocaleString()} candles`}
                    </p>
                  </div>
                )}

                {/* Timestamps */}
                <div className="col-span-2 flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="size-3" />
                    <span>Created: {formatDate(job.created_at)}</span>
                  </div>
                  {job.started_at && (
                    <div className="flex items-center gap-1">
                      <Clock className="size-3" />
                      <span>Duration: {formatDuration(job.started_at, job.completed_at)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Status Detail - Human-readable progress */}
              {job.status_detail && (
                <div className="mt-3 rounded border border-blue-500/30 bg-blue-500/10 p-2 text-xs text-blue-700 dark:text-blue-300 font-medium">
                  {job.status_detail}
                </div>
              )}

              {/* Error Message */}
              {job.status === 'failed' && job.error_message && (
                <div className="mt-3 rounded border border-red-500/50 bg-red-500/10 p-2 text-xs text-red-600 dark:text-red-400">
                  {job.error_message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {page * limit + 1} - {Math.min((page + 1) * limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={(page + 1) * limit >= total}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Logs Modal (FASE 4) */}
      <Dialog open={!!selectedJobForLogs} onOpenChange={(open) => !open && setSelectedJobForLogs(null)}>
        <DialogContent className="max-w-5xl h-[80vh]">
          <DialogHeader>
            <DialogTitle>Job Logs</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-hidden">
            {selectedJobForLogs && (
              <JobLogViewer jobId={selectedJobForLogs} />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
