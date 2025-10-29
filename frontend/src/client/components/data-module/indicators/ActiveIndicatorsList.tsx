import React from "react";
import { Trash2, Eye, EyeOff, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDataModuleStore } from "@/state/data-module.store";

export const ActiveIndicatorsList: React.FC = () => {
  const { indicators, removeIndicator, toggleIndicatorVisibility } = useDataModuleStore();

  if (indicators.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card flex flex-col overflow-hidden">
        <div className="p-4 border-b border-border">
          <h2 className="font-semibold">Active Indicators</h2>
          <p className="text-xs text-muted-foreground mt-1">No indicators added</p>
        </div>
        <div className="p-6 text-center text-sm text-muted-foreground">
          Add indicators from the library to get started
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card flex flex-col overflow-hidden">
      <div className="p-4 border-b border-border sticky top-0 bg-card/95 backdrop-blur">
        <h2 className="font-semibold">Active Indicators</h2>
        <p className="text-xs text-muted-foreground mt-1">{indicators.length} indicator(s)</p>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-border">
        {indicators.map((indicator) => (
          <div key={indicator.id} className="p-3 hover:bg-accent/30 transition-colors">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2 flex-1">
                <div
                  className="size-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: indicator.color }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{indicator.name}</p>
                  <p className="text-xs text-muted-foreground">{indicator.type}</p>
                </div>
              </div>
              <div className="flex gap-1 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => toggleIndicatorVisibility(indicator.id)}
                  title={indicator.visible ? "Hide indicator" : "Show indicator"}
                >
                  {indicator.visible ? (
                    <Eye className="size-3.5" />
                  ) : (
                    <EyeOff className="size-3.5 text-muted-foreground" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  title="Configure parameters"
                >
                  <Settings className="size-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:text-destructive"
                  onClick={() => removeIndicator(indicator.id)}
                  title="Remove indicator"
                >
                  <Trash2 className="size-3.5" />
                </Button>
              </div>
            </div>

            {Object.keys(indicator.parameters).length > 0 && (
              <div className="ml-5 mt-2 space-y-1">
                {Object.entries(indicator.parameters).map(([key, value]) => (
                  <div key={key} className="text-xs text-muted-foreground flex justify-between">
                    <span>{key}:</span>
                    <span className="font-medium text-foreground">{value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
