import React from "react";
import { TopNavbar } from "@/components/layout/TopNavbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { Placeholder } from "@/components/common/Placeholder";

export const WithLayout: React.FC<{ title?: string; description?: string }> = (props) => {
  return (
    <div className="min-h-screen bg-background">
      <TopNavbar />
      <Sidebar />
      <main className="pt-16 pl-14 md:pl-60">
        <Placeholder {...props} />
      </main>
    </div>
  );
};

export default WithLayout;
