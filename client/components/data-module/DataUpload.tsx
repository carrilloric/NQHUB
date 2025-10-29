import React, { useRef } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

interface DataUploadProps {
  onUpload: (file: File) => void;
}

export const DataUpload: React.FC<DataUploadProps> = ({ onUpload }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = React.useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    files.forEach((file) => {
      if (file.type.includes("csv") || file.type.includes("json") || file.type.includes("text")) {
        onUpload(file);
      }
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => onUpload(file));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "relative border-2 border-dashed rounded-lg p-8 transition-all cursor-pointer",
        isDragOver
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/50 hover:bg-accent/30"
      )}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".csv,.json,.txt"
        onChange={handleFileSelect}
        className="hidden"
      />
      <div className="flex flex-col items-center justify-center gap-3">
        <div className={cn(
          "p-3 rounded-lg transition-colors",
          isDragOver ? "bg-primary/20" : "bg-accent/30"
        )}>
          <Upload className={cn("size-6", isDragOver ? "text-primary" : "text-muted-foreground")} />
        </div>
        <div className="text-center">
          <p className="font-semibold">
            {isDragOver ? "Drop files here" : "Drag & drop your data files"}
          </p>
          <p className="text-sm text-muted-foreground">
            or click to browse (CSV, JSON, TXT)
          </p>
        </div>
      </div>
    </div>
  );
};
