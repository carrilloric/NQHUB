import React, { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { DataIngestETLSection } from "@/components/data-module/DataIngestETLSection";
import { ChartsSection } from "@/components/data-module/ChartsSection";
import { PatternDetectionSection } from "@/components/data-module/PatternDetectionSection";
import { MarketStateSection } from "@/components/data-module/market-state/MarketStateSection";
import { AssistantPanelSidebar } from "@/assistant";
import { useI18n } from "@/state/app";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type DataModuleTab = "ingest" | "charts" | "patterns" | "market-state";

interface DataModuleProps {
  defaultTab?: DataModuleTab;
}

export const DataModule: React.FC<DataModuleProps> = ({
  defaultTab = "ingest",
}) => {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<DataModuleTab>(defaultTab);

  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="pl-16 md:pl-64 flex min-h-screen items-start bg-[radial-gradient(circle_at_top_left,_rgba(23,211,218,0.12),_transparent)]">
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-auto px-4 py-8 md:px-10">
            <div className="flex flex-col gap-6">
              <div className="space-y-3">
                <h1 className="text-5xl font-extrabold tracking-tight text-foreground">
                  Data Module
                </h1>
                <p className="text-sm text-muted-foreground/80">
                  Upload and analyze NQ datasets across pipelines and chart
                  views
                </p>
              </div>

              <div className="rounded-3xl border border-border/50 bg-gradient-to-br from-[#121b2d] via-[#0b1523] to-[#090f19] shadow-[0_24px_48px_rgba(0,0,0,0.55)]">
                <Tabs
                  value={activeTab}
                  onValueChange={(value) =>
                    setActiveTab(value as DataModuleTab)
                  }
                  className="flex h-full flex-col"
                >
                  <TabsList className="grid w-full grid-cols-4 px-4">
                    <TabsTrigger value="ingest">
                      🧪 Data Ingest & ETL
                    </TabsTrigger>
                    <TabsTrigger value="charts">📊 Charts</TabsTrigger>
                    <TabsTrigger value="patterns">🔍 Pattern Detection</TabsTrigger>
                    <TabsTrigger value="market-state">📸 Market State</TabsTrigger>
                  </TabsList>

                  <div className="flex-1 overflow-hidden">
                    <TabsContent
                      value="ingest"
                      className="flex h-full flex-col overflow-hidden px-6 pb-8 pt-6"
                    >
                      <DataIngestETLSection />
                    </TabsContent>

                    <TabsContent
                      value="charts"
                      className="flex h-full flex-col overflow-hidden px-0 pb-0 pt-4"
                    >
                      <ChartsSection />
                    </TabsContent>

                    <TabsContent
                      value="patterns"
                      className="flex h-full flex-col overflow-auto px-6 pb-8 pt-6"
                    >
                      <PatternDetectionSection />
                    </TabsContent>

                    <TabsContent
                      value="market-state"
                      className="flex h-full flex-col overflow-auto px-6 pb-8 pt-6"
                    >
                      <MarketStateSection />
                    </TabsContent>
                  </div>
                </Tabs>
              </div>
            </div>
          </div>
        </div>
        <AssistantPanelSidebar />
      </main>
    </div>
  );
};

export default DataModule;
