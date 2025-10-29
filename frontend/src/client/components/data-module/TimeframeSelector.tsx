import React from "react";
import { cn } from "@/lib/utils";

interface TimeframeSelectorProps {
  selectedTimeframe: string;
  onTimeframeChange: (timeframe: string) => void;
}

export const TimeframeSelector: React.FC<TimeframeSelectorProps> = ({
  selectedTimeframe,
  onTimeframeChange,
}) => {
  const timeframes = [
    { value: "30s", label: "30s" },
    { value: "1m", label: "1m" },
    { value: "5m", label: "5m" },
    { value: "15m", label: "15m" },
    { value: "1h", label: "1h" },
    { value: "4h", label: "4h" },
    { value: "1d", label: "1d" },
    { value: "1w", label: "1w" },
  ];

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold mb-3">Timeframes</h2>
      <div className="flex flex-wrap gap-2">
        {timeframes.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => onTimeframeChange(value)}
            className={cn(
              "px-3 py-1.5 rounded-lg border transition-all font-medium text-sm",
              selectedTimeframe === value
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-card border-border hover:border-primary/50 hover:bg-accent/30"
            )}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
};
