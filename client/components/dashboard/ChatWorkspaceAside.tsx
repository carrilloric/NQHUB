import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Mic, Globe, Cog, Paperclip, AudioLines } from "lucide-react";

export const ChatWorkspaceAside: React.FC = () => {
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
    const typingDelay = Math.max(28, Math.floor(3000 / Math.max(full.length, 1)));
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
    <aside className="w-80 border-l border-border bg-card/50 flex flex-col overflow-hidden sticky top-16 min-h-[calc(100vh-4rem)]">
      <div className="flex-1 overflow-auto p-4 flex flex-col justify-end">
        <div className="rounded-2xl border border-input bg-card shadow-lg">
          <div className="relative">
            <textarea
              rows={3}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder=""
              className={cn(
                "w-full resize-none bg-transparent outline-none px-4 py-4 text-sm",
                "placeholder:text-muted-foreground"
              )}
            />
            {value.length === 0 && (
              <div aria-hidden className="pointer-events-none absolute left-4 top-3 text-sm text-muted-foreground">
                {hint}
                <span className="ml-0.5 opacity-40">|</span>
              </div>
            )}
          </div>
          <div className="flex items-center justify-end gap-2 px-3 pb-3 text-muted-foreground">
            <IconChip title="Set sources for search">
              <Globe className="size-4" />
            </IconChip>
            <IconChip title="Choose a model" active>
              <Cog className="size-4" />
            </IconChip>
            <IconChip title="Attach a file">
              <Paperclip className="size-4" />
            </IconChip>
            <IconChip title="Dictation">
              <Mic className="size-4" />
            </IconChip>
            <button
              title="Voice mode"
              className="inline-flex items-center justify-center h-9 w-9 rounded-md bg-primary text-primary-foreground shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring hover:bg-primary/90 transition-colors"
            >
              <AudioLines className="size-4" />
            </button>
          </div>
        </div>
      </div>
      <div className="p-4 border-t border-border text-xs text-muted-foreground text-center">
        Powered by NQHUB Assistant
      </div>
    </aside>
  );
};

const IconChip: React.FC<{ title?: string; active?: boolean; children: React.ReactNode }> = ({
  title,
  active,
  children,
}) => (
  <span
    title={title}
    className={cn(
      "inline-flex h-8 w-8 items-center justify-center rounded-md border transition-colors",
      active ? "bg-secondary border-input" : "border-transparent hover:bg-secondary"
    )}
  >
    {children}
  </span>
);
