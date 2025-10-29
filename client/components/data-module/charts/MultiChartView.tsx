import React from "react";
import { Plus, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CandlestickChart } from "./CandlestickChart";
import { useDataModuleStore } from "@/state/data-module.store";
import { cn } from "@/lib/utils";

interface MultiChartViewProps {
  height?: number;
}

export const MultiChartView: React.FC<MultiChartViewProps> = ({ height = 600 }) => {
  const { charts, currentLayout, addChart, removeChart } = useDataModuleStore();

  const gridClass = {
    "2x2": "grid-cols-2 grid-rows-2",
    "3x1": "grid-cols-3 grid-rows-1",
    "4x1": "grid-cols-4 grid-rows-1",
    custom: "grid-cols-2 grid-rows-2",
  };

  const handleAddChart = () => {
    // TODO: Open a dialog to configure new chart
    const newChart = {
      id: `chart-${Date.now()}`,
      title: "New Chart",
      type: "candlestick" as const,
      timeframe: "1h" as const,
      data: charts[0]?.data || [],
      isDetached: false,
    };
    addChart(newChart);
  };

  if (!charts.length) {
    return (
      <div
        className="flex items-center justify-center rounded-2xl border border-dashed border-border/40 bg-gradient-to-br from-[#151f32] to-[#0c1422] p-10 text-center"
        style={{ height }}
      >
        <div className="space-y-3">
          <p className="text-lg font-semibold uppercase tracking-[0.32em] text-foreground/85">No charts configured</p>
          <p className="text-xs uppercase tracking-[0.26em] text-muted-foreground/70">Add charts to your layout</p>
          <Button
            onClick={handleAddChart}
            size="sm"
            className="rounded-full border border-primary/40 bg-primary/15 text-primary hover:bg-primary/25"
          >
            <Plus className="mr-2 size-4" />
            Add Chart
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between rounded-2xl border border-border/40 bg-[#101a2b]/70 px-5 py-4">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-[0.3em] text-foreground/90">{currentLayout?.name || "Charts"}</h2>
          <p className="text-[0.65rem] uppercase tracking-[0.24em] text-muted-foreground/70">{charts.length} chart(s)</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleAddChart}
            className="rounded-full border border-primary/40 bg-transparent text-primary hover:bg-primary/10"
          >
            <Plus className="mr-1 size-4" />
            Add
          </Button>
        </div>
      </div>

      <div
        className={cn(
          "grid flex-1 gap-4 overflow-auto",
          gridClass[currentLayout?.gridConfig || "2x2"]
        )}
      >
        {charts.map((chart) => (
          <div
            key={chart.id}
            className="group relative overflow-hidden rounded-2xl border border-border/40 bg-[#0c1524]/80"
          >
            <CandlestickChart
              data={chart.data as any}
              title={chart.title}
              height={100}
              showVolume={true}
            />

            <div className="absolute right-3 top-3 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              <Button
                variant="ghost"
                size="sm"
                className="h-9 w-9 rounded-full border border-border/40 bg-transparent p-0 text-muted-foreground/70 hover:border-primary/40 hover:text-primary"
                title="Detach chart"
              >
                <Maximize2 className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-9 w-9 rounded-full border border-border/40 bg-transparent p-0 text-muted-foreground/70 hover:border-bearish/40 hover:text-bearish"
                title="Remove chart"
                onClick={() => removeChart(chart.id)}
              >
                ×
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
