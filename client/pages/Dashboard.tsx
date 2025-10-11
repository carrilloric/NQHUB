import React from "react";
import { TopNavbar } from "@/components/layout/TopNavbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { ModuleLauncher } from "@/components/dashboard/ModuleLauncher";
import { useAuth, useI18n } from "@/state/app";
import { LLMPanel } from "@/components/dashboard/LLMPanel";

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { t } = useI18n();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNavbar />
      <Sidebar />
      <main className="pt-16 pl-14 md:pl-60 p-6">
        <section className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">{t("dashboard.title")}</h1>
          <p className="text-muted-foreground">Welcome{user ? `, ${user.firstName}` : ""}. Choose a module to get started.</p>
        </section>
        <ModuleLauncher />
      </main>
      <LLMPanel />
    </div>
  );
};

export default Dashboard;
