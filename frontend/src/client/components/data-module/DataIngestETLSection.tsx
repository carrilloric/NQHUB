import { ETLDashboard } from "./etl/ETLDashboard";

export const DataIngestETLSection = () => {
  return (
    <div className="flex h-full flex-col gap-8 overflow-hidden">
      <section className="rounded-3xl border border-border/40 bg-[radial-gradient(circle_at_top,_rgba(23,211,218,0.18),_transparent)] bg-[#0b1523] p-6 shadow-[0_20px_40px_rgba(0,0,0,0.45)]">
        <header className="flex flex-col gap-2 pb-4 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <div className="flex-1">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
              Pipeline Monitoring
            </p>
            <h3 className="text-xl font-semibold text-foreground/90">
              ETL orchestration health and job telemetry
            </h3>
          </div>
        </header>

        <div className="max-h-[800px] overflow-y-auto pr-1">
          <ETLDashboard />
        </div>
      </section>
    </div>
  );
};
