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
    <div className="flex flex-1 flex-col gap-6 overflow-hidden">
      {/* Controls */}
      <div className="rounded-3xl border border-border/40 bg-gradient-to-br from-[#141f32] via-[#0f1928] to-[#0a111d] p-6 shadow-inner">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-full border border-primary/40 bg-primary/15 p-2">
            <TrendingUp className="size-4 text-primary" />
          </div>
          <h2 className="text-sm font-bold uppercase tracking-[0.3em] text-foreground/90">NQ Futures Analysis</h2>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="flex flex-col gap-2">
            <label className="text-[0.7rem] font-semibold uppercase tracking-[0.28em] text-muted-foreground/70">Timeframe</label>
            <Select value={selectedTimeframe} onValueChange={(value) => setTimeframe(value as any)}>
              <SelectTrigger className="rounded-full border border-border/40 bg-[#0c1624] text-xs uppercase tracking-[0.26em] text-muted-foreground/80">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent className="bg-card">
                {timeframes.map(({ value, label }) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[0.7rem] font-semibold uppercase tracking-[0.28em] text-muted-foreground/70">Start Date</label>
            <div className="relative">
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="rounded-full border border-border/40 bg-[#0c1624] pl-10 text-xs uppercase tracking-[0.24em] text-muted-foreground/80"
              />
              <Calendar className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/60" />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[0.7rem] font-semibold uppercase tracking-[0.28em] text-muted-foreground/70">End Date</label>
            <div className="relative">
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="rounded-full border border-border/40 bg-[#0c1624] pl-10 text-xs uppercase tracking-[0.24em] text-muted-foreground/80"
              />
              <Calendar className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/60" />
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-4 text-xs uppercase tracking-[0.24em] text-muted-foreground/70">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showVolumeProfile}
              onChange={(e) => setShowVolumeProfile(e.target.checked)}
              className="size-4 rounded border border-border/60 bg-[#0c1624]"
              style={{ accentColor: "hsl(var(--primary))" }}
            />
            <span>Volume Profile</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showDeltaProfile}
              onChange={(e) => setShowDeltaProfile(e.target.checked)}
              className="size-4 rounded border border-border/60 bg-[#0c1624]"
              style={{ accentColor: "hsl(var(--secondary))" }}
            />
            <span>Delta Profile</span>
          </label>
        </div>
      </div>

      {/* Charts and Indicators */}
      <Tabs defaultValue="charts" className="flex flex-1 flex-col overflow-hidden">
        <TabsList className="grid w-full grid-cols-2 border-b border-border/40 bg-[#101a2b]/60 px-2">
          <TabsTrigger value="charts">Charts</TabsTrigger>
          <TabsTrigger value="indicators" className="flex items-center gap-2">
            <Zap className="size-4" />
            Indicators
          </TabsTrigger>
        </TabsList>

        <TabsContent value="charts" className="flex flex-1 overflow-hidden">
          <MultiChartView />
        </TabsContent>

        <TabsContent value="indicators" className="flex flex-1 overflow-hidden">
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
