import React, { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { DataUpload } from "@/components/data-module/DataUpload";
import { FileList } from "@/components/data-module/FileList";
import { NewsList } from "@/components/data-module/NewsList";
import { ChartArea } from "@/components/data-module/ChartArea";
import { TimeframeSelector } from "@/components/data-module/TimeframeSelector";
import { ChatWorkspaceAside } from "@/components/dashboard/ChatWorkspaceAside";
import { useI18n } from "@/state/app";

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  uploadedAt: Date;
  progress: number;
  type: "prices" | "news";
  status: "uploading" | "ready" | "transforming" | "completed" | "error";
  transformations?: {
    timeframe: string;
    status: "pending" | "processing" | "completed";
    completedAt?: Date;
  }[];
}

export const DataModule: React.FC = () => {
  const { t } = useI18n();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("1h");

  const handleFileUpload = (file: File, type: "prices" | "news") => {
    const newFile: UploadedFile = {
      id: Date.now().toString(),
      name: file.name,
      size: file.size,
      uploadedAt: new Date(),
      progress: 0,
      type,
      status: "uploading",
      transformations: type === "prices" ? [
        { timeframe: "30s", status: "pending" },
        { timeframe: "1m", status: "pending" },
        { timeframe: "5m", status: "pending" },
        { timeframe: "15m", status: "pending" },
        { timeframe: "1h", status: "pending" },
        { timeframe: "4h", status: "pending" },
        { timeframe: "1d", status: "pending" },
        { timeframe: "1w", status: "pending" },
      ] : undefined,
    };

    setFiles([newFile, ...files]);

    // Simulate upload progress
    let progress = 0;
    const uploadInterval = setInterval(() => {
      progress += Math.random() * 30;
      if (progress >= 100) {
        progress = 100;
        clearInterval(uploadInterval);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === newFile.id ? { ...f, progress: 100, status: "ready" } : f
          )
        );
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === newFile.id ? { ...f, progress } : f))
        );
      }
    }, 300);
  };

  const handleProcessFile = (fileId: string) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === fileId ? { ...f, status: "transforming" } : f
      )
    );
    simulateTransformations(fileId);
  };

  const simulateTransformations = (fileId: string) => {
    const timeframes = ["30s", "1m", "5m", "15m", "1h", "4h", "1d", "1w"];
    let completedCount = 0;

    timeframes.forEach((timeframe, index) => {
      setTimeout(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId
              ? {
                  ...f,
                  transformations: f.transformations?.map((t) =>
                    t.timeframe === timeframe
                      ? { ...t, status: "processing" as const }
                      : t
                  ) || [],
                }
              : f
          )
        );

        setTimeout(() => {
          completedCount++;
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileId
                ? {
                    ...f,
                    transformations: f.transformations?.map((t) =>
                      t.timeframe === timeframe
                        ? { ...t, status: "completed" as const, completedAt: new Date() }
                        : t
                    ) || [],
                    status: completedCount === timeframes.length ? "completed" : "transforming",
                  }
                : f
            )
          );
        }, 1000 + Math.random() * 1000);
      }, index * 800);
    });
  };

  const handleDeleteFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
    if (selectedFile?.id === fileId) {
      setSelectedFile(null);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="pl-14 md:pl-60 p-0 flex">
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-auto flex flex-col gap-4 p-6">
            <div>
              <h1 className="text-3xl font-bold tracking-tight mb-2">Data Module</h1>
              <p className="text-muted-foreground">Upload and analyze your trading data with multiple timeframe transformations</p>
            </div>

            <DataUpload onUpload={handleFileUpload} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1">
              <div className="lg:col-span-2 flex flex-col gap-4 overflow-hidden">
                {selectedFile?.type === "prices" && (
                  <>
                    <ChartArea selectedFile={selectedFile} selectedTimeframe={selectedTimeframe} />
                    <TimeframeSelector selectedTimeframe={selectedTimeframe} onTimeframeChange={setSelectedTimeframe} />
                  </>
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
                    <p className="font-semibold">Select a file to view content</p>
                    <p className="text-sm">Upload price or news data to get started</p>
                  </div>
                )}
              </div>
              <div className="overflow-hidden flex flex-col gap-4">
                <FileList
                  files={files}
                  fileType="prices"
                  selectedFile={selectedFile}
                  onSelectFile={setSelectedFile}
                  onDeleteFile={handleDeleteFile}
                  onProcessFile={handleProcessFile}
                />
                <NewsList
                  files={files}
                  selectedFile={selectedFile}
                  onSelectFile={setSelectedFile}
                  onDeleteFile={handleDeleteFile}
                />
              </div>
            </div>
          </div>
        </div>
        <ChatWorkspaceAside />
      </main>
    </div>
  );
};

export default DataModule;
