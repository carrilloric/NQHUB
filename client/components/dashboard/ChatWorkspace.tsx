import React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Image, Mic, SendHorizonal, Plus } from "lucide-react";

export const ChatWorkspace: React.FC<{ title?: string }> = ({ title }) => {
  return (
    <section className="min-h-screen flex flex-col items-center">
      <div className="w-full max-w-[4063px] mx-auto flex flex-col justify-center items-center px-4 pt-16 pb-6 mb-[200px]">
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
              <Button size="sm"><SendHorizonal className="size-4"/></Button>
            </div>
          </div>
          <p className="mt-2 text-xs text-muted-foreground text-center">Tip: Shift+Enter for newline</p>
        </div>
      </div>
    </section>
  );
};
