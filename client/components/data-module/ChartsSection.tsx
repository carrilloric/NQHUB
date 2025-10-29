import React, { useState } from "react";
import { Calendar } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

export const ChartsSection: React.FC = () => {
  const [selectedAsset, setSelectedAsset] = useState<string>("AAPL");
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("1h");
  const [startDate, setStartDate] = useState<string>(
    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0]
  );
  const [endDate, setEndDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );

  const assets = [
    "AAPL",
    "GOOGL",
    "MSFT",
    "TSLA",
    "AMZN",
    "META",
    "NVDA",
    "NFLX",
  ];

  const timeframes = [
    { value: "30s", label: "30 seconds" },
    { value: "1m", label: "1 minute" },
    { value: "5m", label: "5 minutes" },
    { value: "15m", label: "15 minutes" },
    { value: "1h", label: "1 hour" },
    { value: "4h", label: "4 hours" },
    { value: "1d", label: "1 day" },
    { value: "1w", label: "1 week" },
  ];

  return (
    <div className="flex-1 flex flex-col gap-4 overflow-hidden">
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold mb-4">Chart Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Asset / Symbol</label>
            <Select value={selectedAsset} onValueChange={setSelectedAsset}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {assets.map((asset) => (
                  <SelectItem key={asset} value={asset}>
                    {asset}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Timeframe</label>
            <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {timeframes.map(({ value, label }) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Start Date</label>
            <div className="relative">
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="pl-10"
              />
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">End Date</label>
            <div className="relative">
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="pl-10"
              />
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 flex-1 flex flex-col items-center justify-center overflow-hidden">
        <div className="w-full h-full flex flex-col items-center justify-center gap-4 text-center text-muted-foreground">
          <div>
            <p className="font-semibold mb-2">📊 Chart Ready</p>
            <p className="text-sm">
              Asset: <span className="font-medium text-foreground">{selectedAsset}</span>
            </p>
            <p className="text-sm">
              Timeframe: <span className="font-medium text-foreground">{selectedTimeframe}</span>
            </p>
            <p className="text-xs mt-2">
              Period: {startDate} to {endDate}
            </p>
          </div>

          <div className="w-full max-w-2xl h-64 bg-accent/20 rounded-lg border border-dashed border-border flex items-center justify-center">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Chart visualization area</p>
              <p className="text-xs text-muted-foreground mt-1">
                Data from database will render here
              </p>
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            Displaying processed data for the selected filters
          </p>
        </div>
      </div>
    </div>
  );
};
