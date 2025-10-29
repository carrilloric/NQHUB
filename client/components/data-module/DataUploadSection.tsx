import React from "react";
import { Upload, Newspaper } from "lucide-react";
import { DataUpload } from "./DataUpload";
import { FileList } from "./FileList";
import { NewsList } from "./NewsList";
import type { UploadedFile } from "@/pages/DataModule";

interface DataUploadSectionProps {
  files: UploadedFile[];
  selectedFile: UploadedFile | null;
  onSelectFile: (file: UploadedFile) => void;
  onDeleteFile: (fileId: string) => void;
  onProcessFile: (fileId: string) => void;
  onUpload: (file: File, type: "prices" | "news") => void;
}

export const DataUploadSection: React.FC<DataUploadSectionProps> = ({
  files,
  selectedFile,
  onSelectFile,
  onDeleteFile,
  onProcessFile,
  onUpload,
}) => {
  return (
    <div className="flex-1 flex flex-col gap-6 overflow-hidden">
      <DataUpload onUpload={onUpload} />

      <div className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 overflow-hidden rounded-3xl border border-border/40 bg-gradient-to-br from-[#121c30] to-[#0b131f] p-6 lg:col-span-2">
          {selectedFile ? (
            <div className="flex flex-1 flex-col justify-between gap-6">
              <div className="flex flex-col items-center justify-center gap-6 text-center">
                <div className="rounded-2xl border border-primary/40 bg-primary/15 p-4">
                  {selectedFile.type === "prices" ? (
                    <Upload className="size-8 text-primary" />
                  ) : (
                    <Newspaper className="size-8 text-secondary" />
                  )}
                </div>
                <div className="space-y-3">
                  <h2 className="text-xl font-bold uppercase tracking-[0.3em] text-foreground/90">{selectedFile.name}</h2>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground/70">
                    {selectedFile.type === "prices" ? "NQ Futures Price Data" : `Uploaded ${selectedFile.uploadedAt.toLocaleDateString()}`}
                  </p>
                </div>
                {selectedFile.type === "prices" && (
                  <div className="w-full rounded-2xl border border-border/40 bg-gradient-to-r from-[#0f1b2c] to-[#0a121e] px-6 py-4 text-left">
                    <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">Timeframe Transformations</p>
                    <p className="mt-2 text-lg font-semibold text-primary">
                      {selectedFile.transformations?.length || 0} formats available
                    </p>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-3 gap-4 text-xs uppercase tracking-[0.24em] text-muted-foreground/70">
                <div className="rounded-xl border border-border/40 bg-[#0c1524] px-4 py-3 text-center font-semibold text-foreground/80">
                  Status
                  <div className={cn("mt-2 text-sm font-bold", selectedFile.status === "completed" ? "text-bullish" : selectedFile.status === "transforming" ? "text-secondary" : "text-muted-foreground/60")}>
                    {selectedFile.status}
                  </div>
                </div>
                <div className="rounded-xl border border-border/40 bg-[#0c1524] px-4 py-3 text-center font-semibold text-foreground/80">
                  Type
                  <div className="mt-2 text-sm font-bold text-primary">{selectedFile.type}</div>
                </div>
                <div className="rounded-xl border border-border/40 bg-[#0c1524] px-4 py-3 text-center font-semibold text-foreground/80">
                  Size
                  <div className="mt-2 text-sm font-bold text-foreground/90">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border/40 bg-[#0d1624] text-center text-muted-foreground">
              <p className="text-lg font-semibold text-foreground/80">No file selected</p>
              <p className="text-xs uppercase tracking-[0.26em] text-muted-foreground/60">Select a file to inspect details</p>
            </div>
          )}
        </div>
        <div className="flex flex-col gap-6">
          <FileList
            files={files}
            fileType="prices"
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
            onDeleteFile={onDeleteFile}
            onProcessFile={onProcessFile}
          />
          <NewsList
            files={files}
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
            onDeleteFile={onDeleteFile}
          />
        </div>
      </div>
    </div>
  );
};
