import { DataUploadSection } from "./DataUploadSection";
import { ETLDashboard } from "./etl/ETLDashboard";
import type { UploadedFile } from "@/pages/DataModule";

interface DataIngestETLSectionProps {
  files: UploadedFile[];
  selectedFile: UploadedFile | null;
  onSelectFile: (file: UploadedFile) => void;
  onDeleteFile: (fileId: string) => void;
  onProcessFile: (fileId: string) => void;
  onUpload: (file: File, type: "prices" | "news") => void;
}

export const DataIngestETLSection = ({
  files,
  selectedFile,
  onSelectFile,
  onDeleteFile,
  onProcessFile,
  onUpload,
}: DataIngestETLSectionProps) => {
  return (
    <div className="flex h-full flex-col gap-8 overflow-hidden">
      <div className="space-y-2">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
          Ingestion Workflow
        </p>
        <h2 className="text-2xl font-semibold text-foreground/90">
          Prepare, validate, and stage datasets for analytics
        </h2>
      </div>

      <DataUploadSection
        files={files}
        selectedFile={selectedFile}
        onSelectFile={onSelectFile}
        onDeleteFile={onDeleteFile}
        onProcessFile={onProcessFile}
        onUpload={onUpload}
      />

      <section className="rounded-3xl border border-border/40 bg-[radial-gradient(circle_at_top,_rgba(23,211,218,0.18),_transparent)] bg-[#0b1523] p-6 shadow-[0_20px_40px_rgba(0,0,0,0.45)]">
        <header className="flex flex-col gap-2 pb-4 sm:flex-row sm:items-end sm:justify-between sm:gap-4">
          <div>
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
              Pipeline Monitoring
            </p>
            <h3 className="text-xl font-semibold text-foreground/90">
              ETL orchestration health and job telemetry
            </h3>
          </div>
          <span className="text-xs uppercase tracking-[0.24em] text-muted-foreground/60">
            Mock data for staging environment insight
          </span>
        </header>

        <div className="max-h-[520px] overflow-y-auto pr-1">
          <ETLDashboard />
        </div>
      </section>
    </div>
  );
};
