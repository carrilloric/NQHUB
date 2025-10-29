import React, { useState } from "react";
import { Calendar, TrendingUp, Zap } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import { MultiChartView } from "./charts/MultiChartView";
import { IndicatorLibrary } from "./indicators/IndicatorLibrary";
import { ActiveIndicatorsList } from "./indicators/ActiveIndicatorsList";
import { useDataModuleStore } from "@/state/data-module.store";

export const ChartsSection: React.FC = () => {
  const { selectedTimeframe, setTimeframe, showVolumeProfile, showDeltaProfile, setShowVolumeProfile, setShowDeltaProfile } = useDataModuleStore();
  const [startDate, setStartDate] = useState<string>(
    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0]
  );
  const [endDate, setEndDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );

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
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="size-5 text-primary" />
            <h2 className="font-semibold text-lg">Chart Analysis</h2>
          </div>
          <p className="text-sm text-muted-foreground">NQ Futures - Price Data Visualization</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-foreground">Timeframe</label>
            <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
              <SelectTrigger className="bg-background">
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

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-foreground">Start Date</label>
            <div className="relative">
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-background pl-10"
              />
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-foreground">End Date</label>
            <div className="relative">
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-background pl-10"
              />
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card flex-1 flex flex-col overflow-hidden">
        <div className="p-6 border-b border-border">
          <h3 className="font-semibold">NQ Futures - {selectedTimeframe} Chart</h3>
          <div className="flex gap-4 mt-3 text-sm">
            <div>
              <p className="text-muted-foreground">Timeframe</p>
              <p className="font-semibold text-foreground">{selectedTimeframe}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Period</p>
              <p className="font-semibold text-foreground">{startDate} to {endDate}</p>
            </div>
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full h-full bg-gradient-to-br from-accent/10 to-accent/5 rounded-lg border border-dashed border-border/50 flex flex-col items-center justify-center gap-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <TrendingUp className="size-6" />
              <p className="text-sm font-medium">Chart visualization area</p>
            </div>
            <p className="text-xs text-muted-foreground">Processed price data from database will be rendered here</p>
          </div>
        </div>
      </div>
    </div>
  );
};
