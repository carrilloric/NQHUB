import React from "react";
import { Activity } from "lucide-react";
import type { UploadedFile } from "@/pages/DataModule";

interface ChartAreaProps {
  selectedFile: UploadedFile | null;
  selectedTimeframe: string;
}

const getTimeframeRange = (date: Date, timeframe: string): { start: Date; end: Date } => {
  const timeframeMinutes: { [key: string]: number } = {
    "30s": 0.5 / 60,
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
  };

  const minutes = timeframeMinutes[timeframe] || 60;
  const start = new Date(date);
  const end = new Date(date.getTime() + minutes * 60 * 1000);

  return { start, end };
};

const formatDateTime = (date: Date): string => {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  }).format(date);
};

export const ChartArea: React.FC<ChartAreaProps> = ({
  selectedFile,
  selectedTimeframe,
}) => {
  const isPricesFile = selectedFile?.type === "prices";
  const timeRange = isPricesFile && selectedFile ? getTimeframeRange(selectedFile.uploadedAt, selectedTimeframe) : null;

  return (
    <div className="rounded-lg border border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-border bg-card/50">
        <h2 className="font-semibold mb-1">Chart Visualization</h2>
        <p className="text-sm text-muted-foreground">
          {selectedFile && timeRange
            ? `${selectedFile.name} - ${selectedTimeframe} timeframe`
            : "Select a file to display chart"}
        </p>
        {selectedFile && timeRange && (
          <p className="text-xs text-muted-foreground mt-1">
            {formatDateTime(timeRange.start)} to {formatDateTime(timeRange.end)}
          </p>
        )}
      </div>

      <div className="flex-1 flex items-center justify-center p-8 text-center text-muted-foreground">
        {!selectedFile ? (
          <div className="flex flex-col items-center gap-3">
            <div className="p-3 rounded-lg bg-accent/30">
              <Activity className="size-8 text-muted-foreground" />
            </div>
            <div>
              <p className="font-medium">No file selected</p>
              <p className="text-sm">Upload and select a data file to visualize it here</p>
            </div>
          </div>
        ) : timeRange ? (
          <div className="w-full h-full flex flex-col items-center justify-center gap-4">
            <div className="text-center max-w-md">
              <p className="font-medium mb-2">Chart for {selectedTimeframe}</p>
              <div className="bg-accent/30 rounded-lg p-3 mb-3">
                <p className="text-sm font-semibold text-foreground">
                  {formatDateTime(timeRange.start)}
                </p>
                <p className="text-xs text-muted-foreground mt-1">to</p>
                <p className="text-sm font-semibold text-foreground">
                  {formatDateTime(timeRange.end)}
                </p>
              </div>
              <p className="text-sm text-muted-foreground">
                Integration with charting library coming soon
              </p>
            </div>
            <div className="w-full h-64 bg-accent/20 rounded-lg border border-dashed border-border flex items-center justify-center">
              <div className="text-center">
                <p className="text-sm text-muted-foreground">Chart visualization area</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Ready to render data from {selectedFile.name}
                </p>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
