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
    <div className="flex-1 flex flex-col gap-4 overflow-hidden">
      <DataUpload onUpload={onUpload} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1">
        <div className="lg:col-span-2 flex flex-col gap-4 overflow-hidden">
          {selectedFile?.type === "prices" && (
            <div className="rounded-lg border border-border bg-card p-8 flex-1 flex flex-col items-center justify-center">
              <div className="text-center max-w-md">
                <div className="flex items-center justify-center mb-4">
                  <div className="p-3 rounded-lg bg-primary/10">
                    <Upload className="size-6 text-primary" />
                  </div>
                </div>
                <p className="font-semibold text-lg mb-2">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground mb-3">
                  NQ Futures price data
                </p>
                <div className="bg-accent/30 rounded-lg p-3 mb-3">
                  <p className="text-xs text-muted-foreground mb-1">Timeframe Transformations</p>
                  <p className="text-sm font-semibold text-foreground">{selectedFile.transformations?.length || 0} formats available</p>
                </div>
                {selectedFile.status === "completed" && (
                  <div className="flex items-center justify-center gap-2 text-green-600 text-sm font-medium">
                    <div className="size-2 rounded-full bg-green-600" />
                    Processing completed
                  </div>
                )}
                {selectedFile.status === "transforming" && (
                  <div className="flex items-center justify-center gap-2 text-blue-600 text-sm font-medium">
                    <div className="size-2 rounded-full bg-blue-600 animate-pulse" />
                    Processing in progress
                  </div>
                )}
              </div>
            </div>
          )}
          {selectedFile?.type === "news" && (
            <div className="rounded-lg border border-border bg-card p-8 flex-1 flex flex-col items-center justify-center">
              <div className="text-center max-w-md">
                <div className="flex items-center justify-center mb-4">
                  <div className="p-3 rounded-lg bg-primary/10">
                    <Newspaper className="size-6 text-primary" />
                  </div>
                </div>
                <p className="font-semibold text-lg mb-2">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  Uploaded on {selectedFile.uploadedAt.toLocaleDateString()}
                </p>
              </div>
            </div>
          )}
          {!selectedFile && (
            <div className="rounded-lg border border-dashed border-border bg-card/50 flex-1 flex flex-col items-center justify-center text-center text-muted-foreground">
              <p className="font-semibold">No file selected</p>
              <p className="text-sm">Select a file from the list to view details</p>
            </div>
          )}
        </div>
        <div className="overflow-hidden flex flex-col gap-4">
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
