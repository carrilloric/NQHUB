import React from "react";
import { PatternDetectionDashboard } from "./patterns/PatternDetectionDashboard";

export const PatternDetectionSection: React.FC = () => {
  return (
    <div className="flex h-full flex-col">
      <div className="space-y-3 mb-6">
        <h2 className="text-2xl font-bold">Pattern Detection</h2>
        <p className="text-sm text-muted-foreground">
          Analyze market structure with Smart Money Concepts: Fair Value Gaps, Liquidity Pools, and Order Blocks
        </p>
      </div>
      <PatternDetectionDashboard />
    </div>
  );
};
