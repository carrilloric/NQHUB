import React, { useCallback, useRef } from "react";
import { useUI } from "@/state/app";
import { Button } from "@/components/ui/button";
import { Image, Mic, SendHorizonal } from "lucide-react";
import { cn } from "@/lib/utils";

export const LLMPanel: React.FC = () => {
  const ui = useUI();
  const startY = useRef<number | null>(null);
  const startH = useRef<number>(ui.llmPanelHeight);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    startY.current = e.clientY;
    startH.current = ui.llmPanelHeight;
    const onMove = (ev: MouseEvent) => {
      if (startY.current == null) return;
      const delta = startY.current - ev.clientY; // dragging up increases height
      const next = Math.min(Math.max(200, startH.current + delta), window.innerHeight - 120);
      ui.setLlmPanelHeight(next);
    };
    const onUp = () => {
      startY.current = null;
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }, [ui]);

  if (!ui.llmPanelOpen) return null;

  return (
    <div className="fixed left-0 right-0 bottom-0 z-30" style={{ height: ui.llmPanelHeight }}>
      <div className="h-3 cursor-ns-resize bg-border/50" onMouseDown={onMouseDown} />
      <div className="h-[calc(100%-12px)] bg-card border-t border-border/60 grid" style={{ gridTemplateColumns: "280px 1fr" }}>
        <ConversationSidebar />
        <div className="flex flex-col">
          <div className="flex-1 overflow-auto p-4 space-y-3">
            <div className="text-sm text-muted-foreground">Ask anything about your data, strategies, or the platform.</div>
          </div>
          <div className="border-t border-border/60 p-3 flex items-center gap-2">
            <input className={cn("flex-1 h-11 rounded-md bg-background px-3 outline-none border border-input focus:ring-2 focus:ring-ring")} placeholder="Ask me anything..." />
            <Button variant="ghost" size="icon" aria-label="Voice"><Mic className="size-5"/></Button>
            <Button variant="ghost" size="icon" aria-label="Image"><Image className="size-5"/></Button>
            <Button><SendHorizonal className="size-4 mr-2"/> Send</Button>
          </div>
        </div>
      </div>
    </div>
  );
};

const ConversationSidebar: React.FC = () => {
  return (
    <div className="border-r border-border/60 bg-background/60 h-full p-3">
      <div className="text-xs font-semibold text-muted-foreground mb-2">Recent</div>
      <div className="space-y-2">
        {["Market recap", "Strategy idea", "Bug report"].map((t) => (
          <button key={t} className="w-full text-left text-sm px-2 py-2 rounded hover:bg-accent/50">
            <div className="font-medium truncate">{t}</div>
            <div className="text-xs text-muted-foreground truncate">Last message preview goes here...</div>
          </button>
        ))}
      </div>
      <Button variant="secondary" className="w-full mt-3">+ New Conversation</Button>
    </div>
  );
};
