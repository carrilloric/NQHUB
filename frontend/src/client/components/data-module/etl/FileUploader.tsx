import React, { useState, useRef } from "react";
import { Upload, X, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { apiClient } from "@/services/api";
import { TIMEFRAMES, type Timeframe, type ETLJob } from "@/types/etl";
import { cn } from "@/lib/utils";
import ZipAnalyzer from "./ZipAnalyzer";

interface FileUploaderProps {
  onUploadSuccess?: (job: ETLJob) => void;
  onUploadError?: (error: string) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedTimeframes, setSelectedTimeframes] = useState<Timeframe[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showAnalyzer, setShowAnalyzer] = useState(false);
  const [fileToAnalyze, setFileToAnalyze] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    // Check file extension
    if (!file.name.toLowerCase().endsWith('.zip')) {
      return 'File must be a ZIP archive';
    }

    // Check file size (max 5GB)
    const maxSize = 5 * 1024 * 1024 * 1024; // 5GB in bytes
    if (file.size > maxSize) {
      return 'File size exceeds 5GB limit';
    }

    return null;
  };

  const handleFileSelect = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setError(null);
    setSuccess(false);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleTimeframeToggle = (timeframe: Timeframe) => {
    setSelectedTimeframes((prev) =>
      prev.includes(timeframe)
        ? prev.filter((tf) => tf !== timeframe)
        : [...prev, timeframe]
    );
  };

  const handleSelectAll = () => {
    setSelectedTimeframes([...TIMEFRAMES]);
  };

  const handleSelectNone = () => {
    setSelectedTimeframes([]);
  };

  const handlePreAnalysis = () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    if (selectedTimeframes.length === 0) {
      setError('Please select at least one timeframe');
      return;
    }

    // Show analyzer instead of uploading directly
    setFileToAnalyze(selectedFile);
    setShowAnalyzer(true);
  };

  const handleAnalyzerConfirm = async (file: File, overwriteExisting: boolean) => {
    setShowAnalyzer(false);
    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      // Simulate progress (real progress would require axios onUploadProgress)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const job = await apiClient.uploadZip(file, selectedTimeframes);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setSuccess(true);
      setIsUploading(false);

      // Reset form after 2 seconds
      setTimeout(() => {
        setSelectedFile(null);
        setSelectedTimeframes([]);
        setSuccess(false);
        setUploadProgress(0);
        setFileToAnalyze(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }, 2000);

      onUploadSuccess?.(job);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Upload failed';
      setError(errorMessage);
      setIsUploading(false);
      setUploadProgress(0);
      onUploadError?.(errorMessage);
    }
  };

  const handleAnalyzerCancel = () => {
    setShowAnalyzer(false);
    setFileToAnalyze(null);
  };

  const handleUpload = handlePreAnalysis;

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setError(null);
    setSuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  };

  return (
    <div className="space-y-6">
      {/* Drag & Drop Zone */}
      <div
        data-testid="file-dropzone"
        className={cn(
          "relative rounded-lg border-2 border-dashed p-8 transition-all",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50",
          isUploading && "pointer-events-none opacity-50"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center justify-center gap-4">
          <div className="rounded-full bg-primary/10 p-4">
            <Upload className="size-8 text-primary" />
          </div>

          <div className="text-center">
            <p className="text-sm font-medium">
              Drag and drop your ZIP file here, or{" "}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-primary hover:underline"
                disabled={isUploading}
              >
                browse files
              </button>
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Maximum file size: 5GB
            </p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleFileInputChange}
            className="hidden"
            data-testid="file-input"
            disabled={isUploading}
          />
        </div>

        {/* Selected File Display */}
        {selectedFile && (
          <div className="mt-4 flex items-center justify-between rounded-lg border border-border bg-accent/20 p-3">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="size-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">{selectedFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemoveFile}
              disabled={isUploading}
              className="size-8 p-0"
            >
              <X className="size-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Timeframe Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Select Timeframes</Label>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSelectAll}
              disabled={isUploading}
              data-testid="select-all-timeframes"
            >
              Select All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSelectNone}
              disabled={isUploading}
              data-testid="select-none-timeframes"
            >
              Clear
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {TIMEFRAMES.map((timeframe) => (
            <div
              key={timeframe}
              className={cn(
                "flex items-center gap-2 rounded-lg border border-border bg-accent/20 p-3 transition-colors",
                selectedTimeframes.includes(timeframe) && "border-primary bg-primary/5"
              )}
            >
              <Checkbox
                id={`timeframe-${timeframe}`}
                checked={selectedTimeframes.includes(timeframe)}
                onCheckedChange={() => handleTimeframeToggle(timeframe)}
                disabled={isUploading}
                data-testid={`timeframe-checkbox-${timeframe}`}
              />
              <Label
                htmlFor={`timeframe-${timeframe}`}
                className="flex-1 cursor-pointer text-sm font-medium"
              >
                {timeframe}
              </Label>
            </div>
          ))}
        </div>

        {selectedTimeframes.length > 0 && (
          <p className="text-xs text-muted-foreground">
            Selected: {selectedTimeframes.join(', ')}
          </p>
        )}
      </div>

      {/* Upload Progress */}
      {isUploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Uploading...</span>
            <span className="font-medium">{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} className="h-2" />
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="size-4 shrink-0" />
          <span data-testid="upload-error">{error}</span>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="flex items-center gap-2 rounded-lg border border-green-500/50 bg-green-500/10 p-3 text-sm text-green-600 dark:text-green-400">
          <CheckCircle2 className="size-4 shrink-0" />
          <span data-testid="upload-success">File uploaded successfully! Processing job created.</span>
        </div>
      )}

      {/* Upload Button */}
      <Button
        onClick={handleUpload}
        disabled={!selectedFile || selectedTimeframes.length === 0 || isUploading}
        className="w-full"
        size="lg"
        data-testid="upload-button"
      >
        {isUploading ? 'Uploading...' : 'Upload and Process'}
      </Button>

      {/* ZIP Analyzer Modal */}
      {showAnalyzer && fileToAnalyze && (
        <ZipAnalyzer
          file={fileToAnalyze}
          onConfirm={handleAnalyzerConfirm}
          onCancel={handleAnalyzerCancel}
        />
      )}
    </div>
  );
};
