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
    <div className="space-y-5 rounded-3xl border border-border/40 bg-gradient-to-br from-[#141f32] via-[#0e1828] to-[#0a111d] p-6 shadow-inner">
      <div className="flex items-center justify-between gap-4">
        <div>
          <label className="mb-2 block text-[0.7rem] font-semibold uppercase tracking-[0.28em] text-muted-foreground/70">
            Data Type
          </label>
          <Select value={selectedType} onValueChange={(value) => setSelectedType(value as "prices" | "news")}>
            <SelectTrigger className="w-48 rounded-full border border-border/40 bg-[#0c1624] text-xs uppercase tracking-[0.28em] text-muted-foreground/80">
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent className="bg-card">
              <SelectItem value="prices" className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-sm">
                  <BarChart3 className="size-4 text-primary" />
                  <span>Price Data</span>
                </div>
              </SelectItem>
              <SelectItem value="news" className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-sm">
                  <Newspaper className="size-4 text-secondary" />
                  <span>News Feed</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <p className="hidden text-[0.65rem] uppercase tracking-[0.26em] text-muted-foreground/60 md:block">
          Drag & drop or browse to ingest datasets
        </p>
      </div>

      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed border-border/40 bg-[linear-gradient(135deg,rgba(15,26,41,0.9),rgba(6,11,19,0.9))] px-6 py-12 text-center transition-all",
          isDragOver ? "border-primary/70 shadow-[0_0_40px_rgba(23,211,218,0.25)]" : "hover:border-primary/40 hover:shadow-[0_0_30px_rgba(23,211,218,0.18)]",
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
        <div className="flex flex-col items-center justify-center gap-4">
          <div
            className={cn(
              "rounded-2xl border border-primary/40 p-4 transition-colors",
              isDragOver ? "bg-primary/20" : "bg-primary/10",
            )}
          >
            <Upload className={cn("size-7", isDragOver ? "text-primary" : "text-primary/80")} />
          </div>
          <div className="space-y-1 text-xs uppercase tracking-[0.28em] text-muted-foreground/80">
            <p className="text-sm font-semibold text-foreground/85">
              {isDragOver ? "Drop files to upload" : "Drag & drop your data files"}
            </p>
            <p>Or click to browse (CSV, JSON, TXT)</p>
          </div>
        </div>
      </div>
    </div>
  );
};
