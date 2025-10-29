import React, { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { DataUploadSection } from "@/components/data-module/DataUploadSection";
import { ChartsSection } from "@/components/data-module/ChartsSection";
import { ETLDashboard } from "@/components/data-module/etl/ETLDashboard";
import { ChatWorkspaceAside } from "@/components/dashboard/ChatWorkspaceAside";
import { useI18n } from "@/state/app";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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
      <main className="pl-16 md:pl-64 flex bg-[radial-gradient(circle_at_top_left,_rgba(23,211,218,0.12),_transparent)]">
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-auto px-4 py-8 md:px-10">
            <div className="flex flex-col gap-6">
              <div className="space-y-2">
                <h1 className="text-4xl font-black uppercase tracking-[0.36em] text-foreground/95">Data Module</h1>
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-muted-foreground/70">
                  Upload and analyze NQ datasets across pipelines and chart views
                </p>
              </div>

              <div className="rounded-3xl border border-border/50 bg-gradient-to-br from-[#121b2d] via-[#0b1523] to-[#090f19] shadow-[0_24px_48px_rgba(0,0,0,0.55)]">
                <Tabs defaultValue="upload" className="flex h-full flex-col">
                  <TabsList className="grid w-full grid-cols-3 px-4">
                    <TabsTrigger value="upload">📤 Data Upload</TabsTrigger>
                    <TabsTrigger value="etl">⚙️ ETL Pipeline</TabsTrigger>
                    <TabsTrigger value="charts">📊 Charts</TabsTrigger>
                  </TabsList>

                  <div className="flex-1 overflow-hidden">
                    <TabsContent value="upload" className="flex h-full flex-col overflow-hidden px-6 pb-8 pt-6">
                      <DataUploadSection
                        files={files}
                        selectedFile={selectedFile}
                        onSelectFile={setSelectedFile}
                        onDeleteFile={handleDeleteFile}
                        onProcessFile={handleProcessFile}
                        onUpload={handleFileUpload}
                      />
                    </TabsContent>

                    <TabsContent value="etl" className="flex h-full flex-col overflow-auto px-6 pb-8 pt-6">
                      <ETLDashboard />
                    </TabsContent>

                    <TabsContent value="charts" className="flex h-full flex-col overflow-hidden px-0 pb-0 pt-4">
                      <ChartsSection />
                    </TabsContent>
                  </div>
                </Tabs>
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
