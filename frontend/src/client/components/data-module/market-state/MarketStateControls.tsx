/**
 * Market State Controls
 *
 * Controls for generating new snapshots or loading existing ones
 */
import React, { useState, useEffect, useRef } from "react";
import { format } from "date-fns";
import { formatInTimeZone, toZonedTime } from "date-fns-tz";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { DatePicker } from "@/components/ui/date-picker";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Clock } from "lucide-react";
import { apiClient } from "@/services/api";
import { MarketStateSnapshotTable } from "./MarketStateSnapshotTable";
import type {
  MarketStateDetailResponse,
  MarketStateListResponse,
  MarketStateGenerateRequest,
  MarketStateProgressResponse
} from "@/types/patterns";

// Helper to format Date to YYYY-MM-DD
const formatDateForAPI = (date: Date | undefined): string => {
  if (!date) return format(new Date(), "yyyy-MM-dd");
  return format(date, "yyyy-MM-dd");
};

interface MarketStateControlsProps {
  onSnapshotLoaded: (snapshot: MarketStateDetailResponse) => void;
  onSnapshotsListLoaded: (list: MarketStateListResponse) => void;
  setLoading: (loading: boolean) => void;
}

export const MarketStateControls: React.FC<MarketStateControlsProps> = ({
  onSnapshotLoaded,
  onSnapshotsListLoaded,
  setLoading
}) => {
  const [symbol, setSymbol] = useState("NQZ5");
  const [startDate, setStartDate] = useState<Date | undefined>(new Date(2025, 10, 24)); // Nov 24, 2025
  const [endDate, setEndDate] = useState<Date | undefined>(new Date(2025, 10, 24));
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("16:00");
  const [intervalMinutes, setIntervalMinutes] = useState(5);

  const [loadSymbol, setLoadSymbol] = useState("NQZ5");
  const [loadDate, setLoadDate] = useState<Date | undefined>(new Date(2025, 10, 24));
  const [loadTime, setLoadTime] = useState("09:30");

  const [generating, setGenerating] = useState(false);
  const [loadingSnapshot, setLoadingSnapshot] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Progress tracking state
  const [progress, setProgress] = useState<MarketStateProgressResponse | null>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Available date range
  const [dateRange, setDateRange] = useState<{ start: string; end: string } | null>(null);

  // Snapshots list for table display
  const [snapshotsList, setSnapshotsList] = useState<MarketStateListResponse | null>(null);

  // Fetch available date range on mount
  useEffect(() => {
    const fetchDateRange = async () => {
      try {
        const list = await apiClient.listMarketStateSnapshots({
          symbol: loadSymbol,
          limit: 1
        });
        if (list.snapshots.length > 0) {
          const firstSnapshot = list.snapshots[0];
          const lastSnapshot = list.snapshots[list.snapshots.length - 1];
          setDateRange({
            start: formatInTimeZone(new Date(firstSnapshot.snapshot_time), 'America/New_York', 'MMM d, yyyy'),
            end: formatInTimeZone(new Date(lastSnapshot.snapshot_time), 'America/New_York', 'MMM d, yyyy')
          });
        }
      } catch (err) {
        console.error('Failed to fetch date range:', err);
      }
    };
    fetchDateRange();
  }, [loadSymbol]);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  // Poll progress for a job
  const startProgressPolling = (jobId: string) => {
    // Clear any existing interval
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    // Store the symbol for later use
    const currentSymbol = symbol;
    const currentStartTime = `${formatDateForAPI(startDate)}T${startTime}:00`;

    // Poll every 500ms
    progressIntervalRef.current = setInterval(async () => {
      try {
        const progressData = await apiClient.getMarketStateProgress(jobId);
        console.log('[Market State] Progress update:', progressData);
        setProgress(progressData);

        // Stop polling if completed or error
        if (progressData.status === "completed" || progressData.status === "error") {
          console.log('[Market State] Stopping polling, status:', progressData.status);
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
            progressIntervalRef.current = null;
          }

          if (progressData.status === "error") {
            setError(progressData.error_message || "Generation failed");
            setGenerating(false);
            setLoading(false);
          } else if (progressData.status === "completed") {
            // Success! Load the first snapshot
            console.log('[Market State] Generation completed! Loading first snapshot...');
            setSuccess(`Generated ${progressData.total_snapshots} snapshots successfully!`);
            setGenerating(false);
            setLoading(false);

            // Auto-load the first snapshot
            await loadSnapshotDetail(currentSymbol, currentStartTime);
          }
        }
      } catch (err) {
        // Job might not exist yet, continue polling
        console.error("[Market State] Error polling progress:", err);
      }
    }, 500);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const request: MarketStateGenerateRequest = {
        symbol,
        start_time: `${formatDateForAPI(startDate)}T${startTime}:00`,
        end_time: `${formatDateForAPI(endDate)}T${endTime}:00`,
        interval_minutes: intervalMinutes
      };

      // Call API which now returns immediately with job_id
      const response = await apiClient.generateMarketState(request);

      console.log('[Market State] API Response:', response);

      // Set initial progress state IMMEDIATELY (before first poll)
      const initialProgress = {
        job_id: response.job_id,
        symbol: response.symbol,
        total_snapshots: response.total_snapshots,
        completed_snapshots: 0,
        percentage: 0,
        status: "running" as const,
        elapsed_seconds: 0,
        estimated_seconds_remaining: 0
      };

      console.log('[Market State] Setting initial progress:', initialProgress);
      setProgress(initialProgress);

      // Start polling progress immediately
      console.log('[Market State] Starting progress polling for job:', response.job_id);
      startProgressPolling(response.job_id);

      // Note: The actual generation happens in background on the server
      // Progress polling will handle completion and loading the first snapshot

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to generate snapshots");
      setGenerating(false);
      setLoading(false);
      setProgress(null);
    }
  };

  const loadSnapshotDetail = async (sym: string, time: string) => {
    setLoadingSnapshot(true);
    setError(null);
    setLoading(true);

    try {
      const detail = await apiClient.getMarketStateDetail(sym, time);
      onSnapshotLoaded(detail);
      setSuccess(`Loaded snapshot for ${sym} at ${detail.snapshot_time_est}`);
    } catch (err: any) {
      let errorMsg = "Failed to load snapshot";

      if (err.response?.status === 404) {
        const estTime = formatInTimeZone(new Date(time), 'America/New_York', 'MMM d, yyyy HH:mm');
        errorMsg = `No snapshot found for ${sym} at ${estTime} EST.`;
        if (dateRange) {
          errorMsg += ` Available data: ${dateRange.start} - ${dateRange.end}.`;
        }
        errorMsg += ' Snapshots are generated at 5-minute intervals (e.g., 09:00, 09:05, 09:10).';
      } else {
        errorMsg = err.response?.data?.detail || err.message || errorMsg;
      }

      setError(errorMsg);
    } finally {
      setLoadingSnapshot(false);
      setLoading(false);
    }
  };

  const handleLoadSnapshot = async () => {
    try {
      // Convert EST input to UTC for API
      const estDateTimeStr = `${formatDateForAPI(loadDate)}T${loadTime}:00`;
      const estDateTime = toZonedTime(estDateTimeStr, 'America/New_York');
      const snapshotTime = formatInTimeZone(estDateTime, 'UTC', "yyyy-MM-dd'T'HH:mm:ss");

      await loadSnapshotDetail(loadSymbol, snapshotTime);
    } catch (err: any) {
      setError(`Invalid date/time: ${err.message}`);
      setLoadingSnapshot(false);
      setLoading(false);
    }
  };

  const handleListSnapshots = async () => {
    setLoadingSnapshot(true);
    setError(null);
    setSuccess(null);
    setSnapshotsList(null); // Clear previous list

    try {
      const list = await apiClient.listMarketStateSnapshots({
        symbol: loadSymbol,
        limit: 100
      });
      onSnapshotsListLoaded(list);
      setSnapshotsList(list); // Store list for table display
      setSuccess(`Found ${list.total} snapshots for ${loadSymbol}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to list snapshots");
    } finally {
      setLoadingSnapshot(false);
    }
  };

  // Handle snapshot selection from table
  const handleTableLoadSnapshot = (symbol: string, snapshotTime: string) => {
    loadSnapshotDetail(symbol, snapshotTime);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Generate Snapshots Card */}
      <Card>
        <CardHeader>
          <CardTitle>Generate New Snapshots</CardTitle>
          <CardDescription>
            Create snapshots for a date/time range
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="gen-symbol">Symbol</Label>
            <Input
              id="gen-symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="NQZ5"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <DatePicker
                date={startDate}
                onDateChange={setStartDate}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="start-time">Start Time</Label>
              <Input
                id="start-time"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label>End Date</Label>
              <DatePicker
                date={endDate}
                onDateChange={setEndDate}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-time">End Time</Label>
              <Input
                id="end-time"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="interval">Interval (minutes)</Label>
            <Select
              value={intervalMinutes.toString()}
              onValueChange={(value) => setIntervalMinutes(parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 minute</SelectItem>
                <SelectItem value="5">5 minutes</SelectItem>
                <SelectItem value="15">15 minutes</SelectItem>
                <SelectItem value="30">30 minutes</SelectItem>
                <SelectItem value="60">60 minutes</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full"
          >
            {generating ? "Generating..." : "Generate Snapshots"}
          </Button>
        </CardContent>
      </Card>

      {/* Load Snapshot Card */}
      <Card>
        <CardHeader>
          <CardTitle>Load Existing Snapshot</CardTitle>
          <CardDescription>
            View a specific snapshot by timestamp
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="load-symbol">Symbol</Label>
            <Input
              id="load-symbol"
              value={loadSymbol}
              onChange={(e) => setLoadSymbol(e.target.value)}
              placeholder="NQZ5"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label>Date (EST)</Label>
              <DatePicker
                date={loadDate}
                onDateChange={setLoadDate}
                className="w-full"
              />
              {dateRange && (
                <p className="text-xs text-muted-foreground">
                  Available: {dateRange.start} - {dateRange.end}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="load-time">Time EST</Label>
              <Input
                id="load-time"
                type="time"
                value={loadTime}
                onChange={(e) => setLoadTime(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                {loadTime && loadDate && (() => {
                  try {
                    // Create EST datetime from date + time inputs
                    const estDateTimeStr = `${formatDateForAPI(loadDate)}T${loadTime}:00`;
                    const estDateTime = toZonedTime(estDateTimeStr, 'America/New_York');
                    // Format as UTC time
                    const utcTime = formatInTimeZone(estDateTime, 'UTC', 'HH:mm');
                    return `UTC: ${utcTime}`;
                  } catch (e) {
                    return 'UTC: --:--';
                  }
                })()}
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleLoadSnapshot}
              disabled={loadingSnapshot}
              className="flex-1"
            >
              {loadingSnapshot ? "Loading..." : "Load Snapshot"}
            </Button>
            <Button
              onClick={handleListSnapshots}
              disabled={loadingSnapshot}
              variant="outline"
              className="flex-1"
            >
              List Available
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Progress Indicator */}
      {progress && (progress.status === "running" || (progress.status === "completed" && progress.percentage < 100)) && (
        <Card className="md:col-span-2 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/50 dark:border-cyan-500/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700 dark:text-cyan-300">
              <Clock className={`h-5 w-5 text-blue-600 dark:text-cyan-400 ${progress.status === "running" ? "animate-spin" : ""}`} />
              {progress.status === "running" ? "Generating Snapshots..." : "Processing..."}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="font-semibold text-blue-900 dark:text-cyan-100">
                  Snapshot {progress.completed_snapshots} / {progress.total_snapshots}
                </span>
                <span className="font-bold text-lg text-blue-700 dark:text-cyan-300">{progress.percentage}%</span>
              </div>
              {/* Progress bar con alto contraste */}
              <div className="relative w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 via-cyan-500 to-blue-600 dark:from-cyan-400 dark:via-blue-400 dark:to-cyan-500 transition-all duration-300 ease-out"
                  style={{ width: `${progress.percentage}%` }}
                >
                  {/* Animated shine effect */}
                  <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 text-sm bg-white/50 dark:bg-gray-800/50 p-3 rounded-lg">
              <div>
                <p className="text-gray-600 dark:text-gray-400 text-xs">Symbol</p>
                <p className="font-bold text-blue-700 dark:text-cyan-300">{progress.symbol}</p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400 text-xs">Elapsed Time</p>
                <p className="font-bold text-blue-700 dark:text-cyan-300">{Math.floor(progress.elapsed_seconds)}s</p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400 text-xs">Est. Remaining</p>
                <p className="font-bold text-blue-700 dark:text-cyan-300">{Math.floor(progress.estimated_seconds_remaining)}s</p>
              </div>
            </div>

            {/* Debug info con mejor contraste */}
            <div className="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 p-2 rounded">
              Status: <span className="font-semibold text-blue-600 dark:text-cyan-400">{progress.status}</span> | Job ID: <span className="font-mono text-gray-700 dark:text-gray-300">{progress.job_id}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status Messages */}
      {error && (
        <Card className="md:col-span-2 border-destructive">
          <CardContent className="pt-6">
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {success && !progress && !snapshotsList && (
        <Card className="md:col-span-2 border-green-500">
          <CardContent className="pt-6">
            <p className="text-sm text-green-600 dark:text-green-400">{success}</p>
          </CardContent>
        </Card>
      )}

      {/* Snapshots List Table */}
      {snapshotsList && (
        <MarketStateSnapshotTable
          data={snapshotsList}
          onLoadSnapshot={handleTableLoadSnapshot}
          loading={loadingSnapshot}
        />
      )}
    </div>
  );
};
