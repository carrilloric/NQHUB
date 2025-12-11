import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FVGDetector } from "./FVGDetector";
import { LiquidityPoolDetector } from "./LiquidityPoolDetector";
import { OrderBlockDetector } from "./OrderBlockDetector";

type PatternTab = "fvg" | "lp" | "ob";

export const PatternDetectionDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PatternTab>("fvg");

  return (
    <div className="space-y-4" data-testid="pattern-detection-dashboard">
      <div className="mb-4">
        <p className="text-sm text-muted-foreground">
          Detect SMC patterns (FVG, Liquidity Pools, Order Blocks) with auto-calibrated parameters.
          Use the generated reports to verify results against your reference samples.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as PatternTab)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="fvg" data-testid="fvg-tab">
            Fair Value Gaps
          </TabsTrigger>
          <TabsTrigger value="lp" data-testid="lp-tab">
            Liquidity Pools
          </TabsTrigger>
          <TabsTrigger value="ob" data-testid="ob-tab">
            Order Blocks
          </TabsTrigger>
        </TabsList>

        <TabsContent value="fvg" className="space-y-4">
          <FVGDetector />
        </TabsContent>

        <TabsContent value="lp" className="space-y-4">
          <LiquidityPoolDetector />
        </TabsContent>

        <TabsContent value="ob" className="space-y-4">
          <OrderBlockDetector />
        </TabsContent>
      </Tabs>
    </div>
  );
};
