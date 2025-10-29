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
            <div className="rounded-lg border border-border bg-card p-6 flex-1 flex flex-col items-center justify-center">
              <div className="text-center max-w-md">
                <p className="text-2xl mb-2">📊</p>
                <p className="font-semibold mb-2">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  Price data file with {selectedFile.transformations?.length || 0} timeframe transformations
                </p>
                {selectedFile.status === "completed" && (
                  <p className="text-xs text-green-600 mt-2">✓ Processing completed</p>
                )}
                {selectedFile.status === "transforming" && (
                  <p className="text-xs text-blue-600 mt-2">⚙ Processing in progress...</p>
                )}
              </div>
            </div>
          )}
          {selectedFile?.type === "news" && (
            <div className="rounded-lg border border-border bg-card p-6 flex-1 flex flex-col items-center justify-center">
              <div className="text-center max-w-md">
                <p className="text-2xl mb-2">📰</p>
                <p className="font-semibold mb-2">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  News content preview would be displayed here. Uploaded on {selectedFile.uploadedAt.toLocaleDateString()}
                </p>
              </div>
            </div>
          )}
          {!selectedFile && (
            <div className="rounded-lg border border-border bg-card flex-1 flex flex-col items-center justify-center text-center text-muted-foreground">
              <p className="font-semibold">Select a file to view details</p>
              <p className="text-sm">Upload price or news data to get started</p>
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
