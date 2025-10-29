import React from "react";
import { Activity } from "lucide-react";
import type { UploadedFile } from "@/pages/DataModule";

interface ChartAreaProps {
  selectedFile: UploadedFile | null;
  selectedTimeframe: string;
}

export const ChartArea: React.FC<ChartAreaProps> = ({
  selectedFile,
  selectedTimeframe,
}) => {
  return (
    <div className="rounded-lg border border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-border bg-card/50">
        <h2 className="font-semibold mb-1">Chart Visualization</h2>
        <p className="text-sm text-muted-foreground">
          {selectedFile
            ? `${selectedFile.name} - ${selectedTimeframe} timeframe`
            : "Select a file to display chart"}
        </p>
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
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-4">
            <div className="text-center">
              <p className="font-medium mb-2">Chart Ready for {selectedTimeframe}</p>
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
            <div className="text-xs text-muted-foreground">
              Timeframe: <span className="font-medium text-foreground">{selectedTimeframe}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
