import React from "react";
import { Trash2, CheckCircle2, AlertCircle, Loader, Newspaper } from "lucide-react";
import { cn } from "@/lib/utils";
import type { UploadedFile } from "@/pages/DataModule";

interface NewsListProps {
  files: UploadedFile[];
  selectedFile: UploadedFile | null;
  onSelectFile: (file: UploadedFile) => void;
  onDeleteFile: (fileId: string) => void;
}

export const NewsList: React.FC<NewsListProps> = ({
  files,
  selectedFile,
  onSelectFile,
  onDeleteFile,
}) => {
  const newsFiles = files.filter(f => f.type === "news");

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="size-4 text-green-500" />;
      case "error":
        return <AlertCircle className="size-4 text-red-500" />;
      case "uploading":
        return <Loader className="size-4 text-blue-500 animate-spin" />;
      default:
        return null;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "uploading":
        return "Uploading";
      case "ready":
        return "Ready";
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

  return (
    <div className="rounded-lg border border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-border bg-card/50 sticky top-0">
        <h2 className="font-semibold flex items-center gap-2">
          <span>📰</span>
          News Files
        </h2>
        <p className="text-xs text-muted-foreground">
          {newsFiles.length} file{newsFiles.length !== 1 ? "s" : ""}
        </p>
      </div>

      <div className="flex-1 overflow-auto">
        {newsFiles.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No news files uploaded
          </div>
        ) : (
          <div className="divide-y divide-border">
            {newsFiles.map((file) => (
              <button
                key={file.id}
                onClick={() => onSelectFile(file)}
                className={cn(
                  "w-full text-left p-3 transition-colors hover:bg-accent/50",
                  selectedFile?.id === file.id && "bg-accent"
                )}
              >
                <div className="flex items-start gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {getStatusIcon(file.status)}
                      <p className="font-medium text-sm truncate">{file.name}</p>
                    </div>
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)} • {formatTime(file.uploadedAt)}
                      </p>
                      <span className="text-xs bg-secondary text-secondary-foreground px-2 py-0.5 rounded">
                        {getStatusLabel(file.status)}
                      </span>
                    </div>

                    {file.status === "uploading" && (
                      <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteFile(file.id);
                    }}
                    className="text-muted-foreground hover:text-foreground transition-colors mt-1"
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
