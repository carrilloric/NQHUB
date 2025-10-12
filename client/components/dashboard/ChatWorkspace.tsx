import React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Image, Mic, SendHorizonal, Plus, Globe, Cog, Paperclip, AudioLines } from "lucide-react";
import { Link } from "react-router-dom";

export const ChatWorkspace: React.FC<{ title?: string }> = ({ title }) => {
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
            <textarea rows={1} placeholder="Ask anything or @mention a Space" className={cn("w-full resize-none bg-transparent outline-none px-4 py-4 text-base", "placeholder:text-muted-foreground")}></textarea>
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
