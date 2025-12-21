/**
 * Market State Section
 *
 * Main component for Market State feature showing active patterns across all 9 timeframes
 */
import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MarketStateControls } from "./MarketStateControls";
import { GlobalMarketStateDashboard } from "./GlobalMarketStateDashboard";
import { AllTimeframesView } from "./AllTimeframesView";
import { SingleTimeframeView } from "./SingleTimeframeView";
import { TIMEFRAMES, TIMEFRAME_LABELS, type Timeframe } from "@/constants/timeframes";
import type {
  MarketStateDetailResponse,
  MarketStateSnapshotInfo,
  MarketStateListResponse
} from "@/types/patterns";

export const MarketStateSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("all");
  const [currentSnapshot, setCurrentSnapshot] = useState<MarketStateDetailResponse | null>(null);
  const [snapshotsList, setSnapshotsList] = useState<MarketStateListResponse | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="space-y-4" data-testid="market-state-section">
      <div className="mb-4">
        <h2 className="text-2xl font-bold mb-2">Market State Snapshots</h2>
        <p className="text-sm text-muted-foreground">
          View active patterns (FVGs, Session Levels, Order Blocks) across all 9 timeframes at specific timestamps.
          Generate snapshots to capture market state or browse historical snapshots.
        </p>
      </div>

      {/* Controls for generating/loading snapshots */}
      <MarketStateControls
        onSnapshotLoaded={setCurrentSnapshot}
        onSnapshotsListLoaded={setSnapshotsList}
        setLoading={setLoading}
      />

      {/* Global Dashboard - always shown when we have a snapshot */}
      {currentSnapshot && (
        <GlobalMarketStateDashboard snapshot={currentSnapshot} />
      )}

      {/* Timeframe Tabs */}
      {currentSnapshot && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-10">
            <TabsTrigger value="all" data-testid="all-timeframes-tab">
              All Timeframes
            </TabsTrigger>
            {TIMEFRAMES.map(tf => (
              <TabsTrigger key={tf} value={tf} data-testid={`${tf}-tab`}>
                {TIMEFRAME_LABELS[tf]}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            <AllTimeframesView snapshot={currentSnapshot} />
          </TabsContent>

          {TIMEFRAMES.map(tf => (
            <TabsContent key={tf} value={tf} className="space-y-4">
              <SingleTimeframeView
                snapshot={currentSnapshot}
                timeframe={tf}
              />
            </TabsContent>
          ))}
        </Tabs>
      )}

      {/* Empty state when no snapshot loaded */}
      {!currentSnapshot && !loading && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Select a symbol and timestamp to load a market state snapshot.</p>
          <p className="text-sm mt-2">Or generate new snapshots for a date range.</p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Loading market state...</p>
        </div>
      )}
    </div>
  );
};
