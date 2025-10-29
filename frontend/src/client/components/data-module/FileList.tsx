import React from "react";
import { Trash2, CheckCircle2, AlertCircle, Loader, Play, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { UploadedFile } from "@/pages/DataModule";

interface FileListProps {
  files: UploadedFile[];
  fileType: "prices" | "news";
  selectedFile: UploadedFile | null;
  onSelectFile: (file: UploadedFile) => void;
  onDeleteFile: (fileId: string) => void;
  onProcessFile: (fileId: string) => void;
}

export const FileList: React.FC<FileListProps> = ({
  files,
  fileType,
  selectedFile,
  onSelectFile,
  onDeleteFile,
  onProcessFile,
}) => {
  const filteredFiles = files.filter(f => f.type === fileType);
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="size-4 text-bullish" />;
      case "error":
        return <AlertCircle className="size-4 text-bearish" />;
      case "uploading":
      case "transforming":
        return <Loader className="size-4 text-primary animate-spin" />;
      default:
        return null;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "uploading":
        return "Uploading";
      case "ready":
        return "Ready to Process";
      case "transforming":
        return "Transforming";
      case "completed":
        return "Completed";
      case "error":
        return "Error";
      default:
        return "Unknown";
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  const getTypeLabel = () => fileType === "prices" ? "Price Files" : "News Files";

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-3xl border border-border/40 bg-gradient-to-br from-[#131d30] to-[#0b141f] shadow-inner">
      <div className="sticky top-0 border-b border-border/40 bg-[#101a2b]/80 px-4 py-4">
        <div className="mb-1 flex items-center gap-2">
          <BarChart3 className="size-4 text-primary" />
          <h2 className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/85">{getTypeLabel()}</h2>
        </div>
        <p className="ml-6 text-[0.65rem] uppercase tracking-[0.24em] text-muted-foreground/70">
          {filteredFiles.length} file{filteredFiles.length !== 1 ? "s" : ""}
        </p>
      </div>

      <div className="flex-1 overflow-auto">
        {filteredFiles.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-muted-foreground/70">
            No {fileType === "prices" ? "price" : "news"} files uploaded
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {filteredFiles.map((file) => (
              <button
                key={file.id}
                onClick={() => onSelectFile(file)}
                className={cn(
                  "w-full px-4 py-4 text-left transition-all hover:bg-primary/10",
                  selectedFile?.id === file.id ? "bg-primary/15 border-l-2 border-primary" : "border-l-2 border-transparent",
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex items-center gap-2">
                      {getStatusIcon(file.status)}
                      <p className="truncate text-sm font-semibold tracking-wide text-foreground/90">{file.name}</p>
                    </div>
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-x-2 gap-y-1 text-[0.68rem] uppercase tracking-[0.22em] text-muted-foreground/70">
                      <span>
                        {formatFileSize(file.size)} • {formatTime(file.uploadedAt)}
                      </span>
                      <span className="rounded-full border border-secondary/40 bg-secondary/15 px-3 py-1 text-secondary">
                        {getStatusLabel(file.status)}
                      </span>
                    </div>

                    {(file.status === "uploading" || file.status === "transforming") && (
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#111f33]">
                        <div
                          className="h-full bg-primary transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    )}

                    {file.transformations && file.transformations.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {file.transformations.map((t) => (
                          <div
                            key={t.timeframe}
                            className={cn(
                              "rounded-full px-3 py-1 text-[0.65rem] uppercase tracking-[0.2em]",
                              t.status === "completed"
                                ? "bg-bullish/15 text-bullish"
                                : t.status === "processing"
                                ? "bg-secondary/20 text-secondary"
                                : "bg-border/40 text-muted-foreground",
                            )}
                          >
                            {t.timeframe}
                          </div>
                        ))}
                      </div>
                    )}

                    {file.status === "ready" && fileType === "prices" && (
                      <div className="mt-4 flex gap-2">
                        <Button
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onProcessFile(file.id);
                          }}
                          className="flex-1 border border-primary/40 bg-primary/15 text-primary hover:bg-primary/25"
                        >
                          <Play className="mr-1 size-3" />
                          Process
                        </Button>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteFile(file.id);
                    }}
                    className="mt-1 text-muted-foreground/70 transition-colors hover:text-bearish"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
