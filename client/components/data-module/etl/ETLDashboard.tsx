import React, { useState, useEffect } from "react";
import { RefreshCw, CheckCircle2, AlertCircle, Loader, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getMockETLStatus, getMockDataSources, getMockETLJobs, type ETLStatus, type DataSource, type ETLJob } from "@/shared/mock-data";

export const ETLDashboard: React.FC = () => {
  const [status, setStatus] = useState<ETLStatus | null>(null);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [jobs, setJobs] = useState<ETLJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load mock data
    setStatus(getMockETLStatus());
    setDataSources(getMockDataSources());
    setJobs(getMockETLJobs());
    setLoading(false);

    // TODO: Replace with actual API calls
    // const fetchETLData = async () => {
    //   try {
    //     const [statusRes, sourcesRes, jobsRes] = await Promise.all([
    //       fetch('/api/etl/status'),
    //       fetch('/api/etl/sources'),
    //       fetch('/api/etl/jobs')
    //     ]);
    //     setStatus(await statusRes.json());
    //     setDataSources(await sourcesRes.json());
    //     setJobs(await jobsRes.json());
    //   } catch (error) {
    //     console.error('Failed to load ETL data:', error);
    //   } finally {
    //     setLoading(false);
    //   }
    // };
    // fetchETLData();
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    // Simulate refresh
    setTimeout(() => {
      setStatus(getMockETLStatus());
      setJobs(getMockETLJobs());
      setLoading(false);
    }, 500);
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case "healthy":
        return "text-green-600 bg-green-500/10";
      case "warning":
        return "text-yellow-600 bg-yellow-500/10";
      case "error":
        return "text-red-600 bg-red-500/10";
      default:
        return "text-muted-foreground";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="size-4 text-green-600" />;
      case "running":
        return <Loader className="size-4 text-blue-600 animate-spin" />;
      case "failed":
        return <AlertCircle className="size-4 text-red-600" />;
      case "scheduled":
        return <Database className="size-4 text-muted-foreground" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Status Overview */}
      {status && (
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">ETL Pipeline Status</h2>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
              className="h-8 w-8 p-0"
            >
              <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg bg-accent/20 p-4">
              <p className="text-sm text-muted-foreground mb-1">Status</p>
              <div className="flex items-center gap-2">
                <div className={`size-2 rounded-full ${status.isRunning ? "bg-green-600 animate-pulse" : "bg-muted-foreground"}`} />
                <p className="font-semibold">{status.isRunning ? "Running" : "Idle"}</p>
              </div>
            </div>

            <div className="rounded-lg bg-accent/20 p-4">
              <p className="text-sm text-muted-foreground mb-1">Total Records</p>
              <p className="text-2xl font-bold">{(status.totalRecords / 1000000).toFixed(1)}M</p>
            </div>

            <div className={`rounded-lg p-4 ${getHealthColor(status.health)}`}>
              <p className="text-sm mb-1">System Health</p>
              <p className="font-semibold capitalize">{status.health}</p>
            </div>
          </div>

          <div className="mt-3 text-xs text-muted-foreground">
            Last update: {new Date(status.lastUpdate).toLocaleTimeString()}
          </div>
        </div>
      )}

      {/* Data Sources */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold">Data Sources</h3>
        </div>
        <div className="divide-y divide-border">
          {dataSources.map((source) => (
            <div key={source.id} className="p-4 hover:bg-accent/30 transition-colors">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex-1">
                  <p className="font-medium text-sm">{source.name}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Provider: <span className="capitalize">{source.provider}</span>
                  </p>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                  source.status === "connected"
                    ? "bg-green-500/20 text-green-700"
                    : source.status === "error"
                    ? "bg-red-500/20 text-red-700"
                    : "bg-yellow-500/20 text-yellow-700"
                }`}>
                  {source.status}
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Instruments: {source.instruments.join(", ")}</span>
                <span>Synced: {new Date(source.lastSync).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ETL Jobs */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold">ETL Jobs</h3>
        </div>
        <div className="divide-y divide-border max-h-96 overflow-y-auto">
          {jobs.map((job) => (
            <div key={job.id} className="p-4 hover:bg-accent/30 transition-colors">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2 flex-1">
                  {getStatusIcon(job.status)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm">{job.name}</p>
                    <p className="text-xs text-muted-foreground">{job.dataSource}</p>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                  job.status === "completed"
                    ? "bg-green-500/20 text-green-700"
                    : job.status === "running"
                    ? "bg-blue-500/20 text-blue-700"
                    : job.status === "failed"
                    ? "bg-red-500/20 text-red-700"
                    : "bg-muted/50 text-muted-foreground"
                }`}>
                  {job.status}
                </div>
              </div>

              {(job.status === "running" || job.progress > 0) && (
                <div className="mb-2">
                  <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{job.progress}% · {job.recordsProcessed.toLocaleString()} records</p>
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Started: {new Date(job.startTime).toLocaleTimeString()}</span>
                {job.endTime && <span>Finished: {new Date(job.endTime).toLocaleTimeString()}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
