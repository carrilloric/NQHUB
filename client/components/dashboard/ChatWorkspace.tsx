import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Image, Mic, SendHorizonal, Plus, Globe, Cog, Paperclip, AudioLines } from "lucide-react";
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
    let delay = isDeleting ? 28 : 55;

    if (!isDeleting && hint === full) {
      delay = 1400;
      setIsDeleting(true);
    } else if (isDeleting && hint === "") {
      setIsDeleting(false);
      setIdx((i) => (i + 1) % suggestions.length);
      delay = 450;
    } else {
      const next = isDeleting ? full.slice(0, hint.length - 1) : full.slice(0, hint.length + 1);
      setHint(next);
    }

    const t = setTimeout(() => {}, delay);
    return () => clearTimeout(t);
  }, [hint, isDeleting, idx]);
  return (
    <section className="min-h-screen flex flex-col items-center">
      <div className="w-full max-w-3xl mx-auto flex flex-col justify-end items-center px-4 pb-16" style={{ minHeight: "80vh" }}>
        <div className="text-center mb-6">
          <div className="text-5xl font-extrabold tracking-tight"><span className="text-primary">NQ</span>HUB</div>
          {title && <p className="mt-2 text-sm text-muted-foreground">{title}</p>}
        </div>
        <div className="w-full">
          <div className="rounded-2xl border border-input bg-card shadow-lg">
            <div className="flex items-center gap-2 px-3 pt-3">
              <Button variant="secondary" size="sm" className="rounded-lg px-2"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg></Button>
              <Button variant="secondary" size="sm" className="rounded-lg px-2"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 3v4"></path><path d="M19 3v4"></path><rect width="14" height="12" x="5" y="7" rx="2"></rect></svg></Button>
              <Button variant="secondary" size="sm" className="rounded-lg px-2"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v18"></path><path d="M3 12h18"></path></svg></Button>
            </div>
            <div className="relative">
              <textarea
                rows={1}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder=""
                className={cn("w-full resize-none bg-transparent outline-none px-4 py-4 text-base", "placeholder:text-muted-foreground")}
              />
              {value.length === 0 && (
                <div aria-hidden className="pointer-events-none absolute left-4 top-3 text-base text-muted-foreground">
                  {hint}
                  <span className="ml-0.5 opacity-40">|</span>
                </div>
              )}
            </div>
            <div className="flex items-center justify-end gap-2 px-3 pb-3 text-muted-foreground">
              <IconChip title="Set sources for search"><Globe className="size-4" /></IconChip>
              <IconChip title="Choose a model" active><Cog className="size-4" /></IconChip>
              <IconChip title="Attach a file"><Paperclip className="size-4" /></IconChip>
              <IconChip title="Dictation"><Mic className="size-4" /></IconChip>
              <button title="Voice mode" className="inline-flex items-center justify-center h-9 w-9 rounded-md bg-primary text-primary-foreground shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                <AudioLines className="size-4" />
              </button>
            </div>
          </div>
        </div>
        <div className="mt-6 flex flex-wrap gap-3 justify-center">
          <QuickPill to="/data" label="Data Module" />
          <QuickPill to="/stats" label="NQ Stats" />
          <QuickPill to="/backtesting" label="BackTesting" />
          <QuickPill to="/tradecademy" label="Tradecademy" />
        </div>
      </div>
    </section>
  );
};

const QuickPill: React.FC<{ to: string; label: string }> = ({ to, label }) => (
  <Link to={to} className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/20 px-3 py-1.5 text-sm shadow hover:bg-accent/30 transition-colors">
    {label}
  </Link>
);

const IconChip: React.FC<{ title?: string; active?: boolean; children: React.ReactNode }> = ({ title, active, children }) => (
  <span title={title} className={cn("inline-flex h-8 w-8 items-center justify-center rounded-md border transition-colors", active ? "bg-secondary border-input" : "border-transparent hover:bg-secondary")}>
    {children}
  </span>
);
