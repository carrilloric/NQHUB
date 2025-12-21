/**
 * Single Timeframe View
 *
 * Shows detailed pattern information for a single timeframe
 */
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TIMEFRAME_LABELS, type Timeframe } from "@/constants/timeframes";
import { MarketStatePatternTable } from "./MarketStatePatternTable";
import type { MarketStateDetailResponse } from "@/types/patterns";

interface SingleTimeframeViewProps {
  snapshot: MarketStateDetailResponse;
  timeframe: Timeframe;
}

export const SingleTimeframeView: React.FC<SingleTimeframeViewProps> = ({
  snapshot,
  timeframe
}) => {
  const tfData = snapshot.timeframes[timeframe];

  if (!tfData) {
    return (
      <Card>
        <CardContent className="text-center py-12 text-muted-foreground">
          <p>No data available for {TIMEFRAME_LABELS[timeframe]}</p>
        </CardContent>
      </Card>
    );
  }

  const { summary, active_fvgs, active_session_levels, active_obs } = tfData;

  return (
    <div className="space-y-4">
      {/* Timeframe Summary */}
      <Card>
        <CardHeader>
          <CardTitle>{TIMEFRAME_LABELS[timeframe]} Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Patterns</p>
              <p className="text-2xl font-bold">
                {summary.active_fvgs_count + summary.active_lps_count + summary.active_obs_count}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Fair Value Gaps</p>
              <p className="text-2xl font-bold">{summary.active_fvgs_count}</p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Session Levels</p>
              <p className="text-2xl font-bold">{summary.active_lps_count}</p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Order Blocks</p>
              <p className="text-2xl font-bold">{summary.active_obs_count}</p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Bullish / Bearish</p>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold text-green-600 dark:text-green-400">
                  {summary.bullish_count}
                </span>
                <span className="text-muted-foreground">/</span>
                <span className="text-xl font-bold text-red-600 dark:text-red-400">
                  {summary.bearish_count}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pattern Tables */}
      <MarketStatePatternTable
        fvgs={active_fvgs}
        sessionLevels={active_session_levels}
        orderBlocks={active_obs}
      />
    </div>
  );
};
