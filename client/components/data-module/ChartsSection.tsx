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
      {/* Controls */}
      <div className="rounded-lg border border-border bg-card p-4 space-y-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-5 text-primary" />
          <h2 className="font-semibold">NQ Futures Analysis</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-foreground">Timeframe</label>
            <Select value={selectedTimeframe} onValueChange={(value) => setTimeframe(value as any)}>
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

        <div className="flex gap-4 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showVolumeProfile}
              onChange={(e) => setShowVolumeProfile(e.target.checked)}
              className="rounded border border-border"
            />
            <span>Volume Profile</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showDeltaProfile}
              onChange={(e) => setShowDeltaProfile(e.target.checked)}
              className="rounded border border-border"
            />
            <span>Delta Profile</span>
          </label>
        </div>
      </div>

      {/* Charts and Indicators */}
      <Tabs defaultValue="charts" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="charts">Charts</TabsTrigger>
          <TabsTrigger value="indicators" className="flex items-center gap-2">
            <Zap className="size-4" />
            Indicators
          </TabsTrigger>
        </TabsList>

        <TabsContent value="charts" className="flex-1 overflow-hidden">
          <MultiChartView />
        </TabsContent>

        <TabsContent value="indicators" className="flex-1 overflow-hidden">
          <ResizablePanelGroup direction="horizontal" className="h-full">
            <ResizablePanel defaultSize={50} minSize={30}>
              <IndicatorLibrary />
            </ResizablePanel>
            <ResizableHandle />
            <ResizablePanel defaultSize={50} minSize={30}>
              <ActiveIndicatorsList />
            </ResizablePanel>
          </ResizablePanelGroup>
        </TabsContent>
      </Tabs>
    </div>
  );
};
