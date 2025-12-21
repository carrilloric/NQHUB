import React from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Placeholder } from "@/components/common/Placeholder";
import { AssistantPanelSidebar } from "@/assistant";

export const WithLayout: React.FC<{ title?: string; description?: string }> = (props) => {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="pl-16 md:pl-64 flex min-h-screen items-start bg-[radial-gradient(circle_at_top_left,_rgba(23,211,218,0.12),_transparent)]">
        <div className="flex flex-1 flex-col overflow-hidden">
          <Placeholder {...props} />
        </div>
        <AssistantPanelSidebar />
      </main>
    </div>
  );
};

export default WithLayout;
