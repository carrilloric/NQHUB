import React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Image, Mic, SendHorizonal, Plus } from "lucide-react";
import { Link } from "react-router-dom";

export const ChatWorkspace: React.FC<{ title?: string }> = ({ title }) => {
  return (
    <section className="min-h-screen flex flex-col items-center">
      <div className="w-full max-w-3xl mx-auto flex flex-col justify-center items-center px-4 pt-24 pb-12">
        <div className="text-center mb-6">
          <div className="text-5xl font-extrabold tracking-tight"><span className="text-primary">NQ</span>HUB</div>
          {title && <p className="mt-2 text-sm text-muted-foreground">{title}</p>}
        </div>
        <div className="w-full">
          <div className="rounded-2xl border border-input bg-card shadow-sm">
            <div className="flex items-center gap-2 px-3 pt-3">
              <Button variant="secondary" size="sm" className="rounded-lg px-2"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg></Button>
              <Button variant="secondary" size="sm" className="rounded-lg px-2"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 3v4"></path><path d="M19 3v4"></path><rect width="14" height="12" x="5" y="7" rx="2"></rect></svg></Button>
              <Button variant="secondary" size="sm" className="rounded-lg px-2"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v18"></path><path d="M3 12h18"></path></svg></Button>
            </div>
            <textarea rows={1} placeholder="Ask anything or @mention a Space" className={cn("w-full resize-none bg-transparent outline-none px-4 py-4 text-base", "placeholder:text-muted-foreground")}></textarea>
            <div className="flex items-center justify-between px-3 pb-3">
              <div className="flex items-center gap-3 text-muted-foreground">
                <svg className="size-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="m2 12 3 1 2 5 3-7 2 3 2-2 3 1 3-3"></path></svg>
                <svg className="size-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M2 12h20"></path><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                <svg className="size-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" x2="12" y1="15" y2="3"></line></svg>
                <svg className="size-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
                <Mic className="size-4" />
              </div>
              <Button size="sm" className="rounded-lg px-3"><SendHorizonal className="size-4"/></Button>
            </div>
          </div>
        </div>
        <div className="mt-6 flex flex-wrap gap-3 justify-center">
          <QuickPill to="/data" label="Data Module" />
          <QuickPill to="/stats" label="Stats" />
          <QuickPill to="/backtesting" label="BackTesting" />
          <QuickPill to="/tradecademy" label="Tradecademy" />
        </div>
      </div>
    </section>
  );
};

const QuickPill: React.FC<{ to: string; label: string }> = ({ to, label }) => (
  <Link to={to} className="inline-flex items-center gap-2 rounded-full border border-input bg-card px-3 py-1.5 text-sm shadow-sm hover:bg-accent/40">
    {label}
  </Link>
);
