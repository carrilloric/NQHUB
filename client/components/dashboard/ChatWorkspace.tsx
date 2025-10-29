import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Mic, Globe, Cog, Paperclip, AudioLines } from "lucide-react";
import { Link } from "react-router-dom";

export const ChatWorkspace: React.FC<{ title?: string }> = ({ title }) => {
  const suggestions = [
    "Please find the most recent OB in any temporality.",
    "Which are the biggest volume of the last week?",
    "Which are the Highest and the Lowest price the last month?",
  ];
  const [hint, setHint] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [idx, setIdx] = useState(0);
  const [value, setValue] = useState("");

  useEffect(() => {
    const full = suggestions[idx];
    const typingDelay = Math.max(28, Math.floor(3000 / Math.max(full.length, 1))); // ~3s per phrase
    const deletingDelay = Math.max(18, Math.floor(1600 / Math.max(full.length, 1)));

    const atEnd = hint === full && !isDeleting;
    const atStart = hint === "" && isDeleting;

    const delay = atEnd ? 1200 : atStart ? 450 : isDeleting ? deletingDelay : typingDelay;

    const t = setTimeout(() => {
      if (atEnd) {
        setIsDeleting(true);
        return;
      }
      if (atStart) {
        setIsDeleting(false);
        setIdx((i) => (i + 1) % suggestions.length);
        return;
      }
      const next = isDeleting ? full.slice(0, hint.length - 1) : full.slice(0, hint.length + 1);
      setHint(next);
    }, delay);

    return () => clearTimeout(t);
  }, [hint, isDeleting, idx, suggestions]);
  return (
    <section className="relative flex min-h-[calc(100vh-4rem)] w-full flex-col items-center justify-start overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(23,211,218,0.12),_transparent)] pb-20 pt-10">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgba(11,17,29,0.95),rgba(6,10,18,0.92))]" aria-hidden />
      <div className="relative z-10 mx-auto flex w-full max-w-5xl flex-col gap-10 px-4 md:px-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-5xl font-black uppercase tracking-[0.42em] text-foreground/95">
              <span className="text-secondary">NQ</span>HUB
            </div>
            {title && (
              <p className="mt-3 text-xs font-semibold uppercase tracking-[0.32em] text-muted-foreground/70">
                {title}
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3 text-right text-xs uppercase tracking-[0.28em] text-muted-foreground/70">
            <StatBlock label="Open" value="15,182" trend="bullish" />
            <StatBlock label="High" value="15,342" trend="bullish" />
            <StatBlock label="Low" value="15,021" trend="bearish" />
            <StatBlock label="Volume" value="3.2M" />
          </div>
        </div>

        <div className="rounded-3xl border border-border/40 bg-gradient-to-br from-[#131d2f] via-[#0c1523] to-[#09101b] shadow-[0_24px_48px_rgba(0,0,0,0.55)]">
          <div className="relative">
            <textarea
              rows={1}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder=""
              className={cn(
                "w-full resize-none bg-transparent px-6 py-7 text-base text-foreground/90 outline-none",
                "placeholder:text-muted-foreground",
              )}
            />
            {value.length === 0 && (
              <div aria-hidden className="pointer-events-none absolute left-6 top-6 text-base text-muted-foreground/60">
                {hint}
                <span className="ml-0.5 opacity-40">|</span>
              </div>
            )}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/40 bg-[#0b1523]/80 px-6 py-4">
            <div className="flex items-center gap-2 text-muted-foreground/80">
              <IconChip title="Data Sources">
                <Globe className="size-4" />
              </IconChip>
              <IconChip title="Models" active>
                <Cog className="size-4" />
              </IconChip>
              <IconChip title="Attach">
                <Paperclip className="size-4" />
              </IconChip>
              <IconChip title="Dictation">
                <Mic className="size-4" />
              </IconChip>
              <IconChip title="Voice Mode" highlight>
                <AudioLines className="size-4" />
              </IconChip>
            </div>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border border-primary/50 bg-primary/15 px-6 py-2 text-[0.72rem] font-semibold uppercase tracking-[0.32em] text-primary transition-colors hover:bg-primary/25"
            >
              Execute
            </button>
          </div>
        </div>

        <div className="grid gap-3 text-xs">
          <span className="font-semibold uppercase tracking-[0.32em] text-muted-foreground/70">Quick Access</span>
          <div className="grid gap-2 md:grid-cols-4">
            <QuickPill to="/data" label="Data Module" />
            <QuickPill to="/stats" label="NQ Stats" />
            <QuickPill to="/backtesting" label="BackTesting" />
            <QuickPill to="/tradecademy" label="Tradecademy" />
          </div>
        </div>
      </div>
    </section>
  );
};

const QuickPill: React.FC<{ to: string; label: string }> = ({ to, label }) => (
  <Link
    to={to}
    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-border/40 bg-gradient-to-br from-[#111b2c] to-[#0b131f] px-4 py-3 text-xs font-semibold uppercase tracking-[0.26em] text-muted-foreground/75 transition-all hover:border-primary/40 hover:text-primary"
  >
    {label}
  </Link>
);

const IconChip: React.FC<{ title?: string; active?: boolean; highlight?: boolean; children: React.ReactNode }> = ({ title, active, highlight, children }) => (
  <span
    title={title}
    className={cn(
      "inline-flex h-9 w-9 items-center justify-center rounded-full border transition-all",
      highlight
        ? "border-primary/50 bg-primary/15 text-primary"
        : active
        ? "border-secondary/50 bg-secondary/20 text-secondary"
        : "border-border/40 bg-transparent text-muted-foreground/70 hover:border-primary/40 hover:text-primary",
    )}
  >
    {children}
  </span>
);

const StatBlock: React.FC<{ label: string; value: string; trend?: "bullish" | "bearish" }> = ({ label, value, trend }) => (
  <div className="rounded-xl border border-border/40 bg-gradient-to-br from-[#111b22] to-[#0b121d] px-4 py-3 text-left shadow-inner">
    <div className="text-[0.6rem] font-semibold uppercase tracking-[0.28em] text-muted-foreground/70">{label}</div>
    <div className={cn("mt-2 text-lg font-bold tabular-nums", trend === "bullish" ? "text-bullish" : trend === "bearish" ? "text-bearish" : "text-foreground/90")}>{value}</div>
  </div>
);
