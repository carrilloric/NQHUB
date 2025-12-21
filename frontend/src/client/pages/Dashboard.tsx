import React from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNavbar } from "@/components/layout/TopNavbar";
import { useI18n } from "@/state/app";
import { AssistantPanelCenter } from "@/assistant";

const Dashboard: React.FC = () => {
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNavbar />
      <Sidebar />
      <main className="pl-14 md:pl-60 pt-16 p-0 flex flex-col">
        <AssistantPanelCenter title={t("dashboard.title")} />
      </main>
    </div>
  );
};

export default Dashboard;
