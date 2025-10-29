import React, { useRef } from "react";
import { Upload, BarChart3, Newspaper } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface DataUploadProps {
  onUpload: (file: File, type: "prices" | "news") => void;
}

export const DataUpload: React.FC<DataUploadProps> = ({ onUpload }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [selectedType, setSelectedType] = React.useState<"prices" | "news">("prices");

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
        onUpload(file, selectedType);
      }
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => onUpload(file, selectedType));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Select value={selectedType} onValueChange={(value) => setSelectedType(value as "prices" | "news")}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="prices">📊 Prices</SelectItem>
            <SelectItem value="news">📰 News</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">Select data type before uploading</p>
      </div>

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
    </div>
  );
};
