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
      <div className="flex items-center justify-center rounded-lg border border-dashed border-border bg-card/50 p-8" style={{ height }}>
        <div className="text-center">
          <p className="font-semibold mb-2">No charts configured</p>
          <p className="text-sm text-muted-foreground mb-4">Add charts to your layout</p>
          <Button onClick={handleAddChart} size="sm">
            <Plus className="size-4 mr-2" />
            Add Chart
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="flex items-center justify-between px-4 py-2">
        <div>
          <h2 className="font-semibold">{currentLayout?.name || "Charts"}</h2>
          <p className="text-xs text-muted-foreground">{charts.length} chart(s)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleAddChart}>
            <Plus className="size-4 mr-1" />
            Add
          </Button>
        </div>
      </div>

      <div
        className={cn(
          "grid gap-4 flex-1 overflow-auto",
          gridClass[currentLayout?.gridConfig || "2x2"]
        )}
      >
        {charts.map((chart) => (
          <div
            key={chart.id}
            className="relative rounded-lg border border-border overflow-hidden bg-card group"
          >
            <CandlestickChart
              data={chart.data as any}
              title={chart.title}
              height={100}
              showVolume={true}
            />

            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                title="Detach chart"
              >
                <Maximize2 className="size-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
