import React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Image, Mic, SendHorizonal, Plus } from "lucide-react";

export const ChatWorkspace: React.FC<{ title?: string }> = ({ title }) => {
  return (
    <div className="min-h-screen grid" style={{ gridTemplateColumns: "280px 1fr" }}>
      <div className="border-r border-border/60 bg-background/60 p-4 hidden md:block">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-semibold text-muted-foreground">Conversations</div>
          <Button variant="secondary" size="sm"><Plus className="size-4 mr-1"/>New</Button>
        </div>
        <div className="space-y-2">
          {["Welcome", "Market recap", "Strategy idea"].map((t) => (
            <button key={t} className="w-full text-left px-3 py-2 rounded hover:bg-accent/50">
              <div className="text-sm font-medium truncate">{t}</div>
              <div className="text-xs text-muted-foreground truncate">Last message preview…</div>
            </button>
          ))}
        </div>
      </div>
      <section className="min-h-screen flex flex-col items-center">
        <div className="w-full max-w-3xl mx-auto px-4 pt-16 pb-6">
          <div className="text-center mb-8">
            <div className="text-3xl font-extrabold tracking-tight"><span className="text-primary">NQ</span>HUB</div>
            {title && <p className="mt-1 text-sm text-muted-foreground">{title}</p>}
          </div>
          <div className="flex-1 min-h-[300px]" />
          <div className="sticky bottom-0">
            <div className="border border-input bg-card rounded-xl p-2 shadow-sm">
              <textarea rows={1} placeholder="Ask anything..." className={cn("w-full resize-none bg-transparent outline-none px-3 py-3 text-base", "placeholder:text-muted-foreground")}></textarea>
              <div className="flex items-center justify-between px-2 pb-1">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm"><Mic className="size-4 mr-1"/>Voice</Button>
                  <Button variant="ghost" size="sm"><Image className="size-4 mr-1"/>Image</Button>
                </div>
                <Button size="sm"><SendHorizonal className="size-4 mr-1"/>Send</Button>
              </div>
            </div>
            <p className="mt-2 text-xs text-muted-foreground text-center">Tip: Shift+Enter for newline</p>
          </div>
        </div>
      </section>
    </div>
  );
};
