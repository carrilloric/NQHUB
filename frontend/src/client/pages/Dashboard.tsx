import React from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { useI18n } from "@/state/app";
import { ChatWorkspace } from "@/components/dashboard/ChatWorkspace";

const Dashboard: React.FC = () => {
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="pl-14 md:pl-60 p-0 flex flex-col">
        <ChatWorkspace title={t("dashboard.title")} />
      </main>
    </div>
  );
};

export default Dashboard;
