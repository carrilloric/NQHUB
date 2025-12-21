/**
 * All Timeframes View
 *
 * Shows summary cards for all 9 timeframes in a grid
 */
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TIMEFRAMES, TIMEFRAME_LABELS, type Timeframe } from "@/constants/timeframes";
import type { MarketStateDetailResponse } from "@/types/patterns";

interface AllTimeframesViewProps {
  snapshot: MarketStateDetailResponse;
}

export const AllTimeframesView: React.FC<AllTimeframesViewProps> = ({ snapshot }) => {
  return (
    <div className="space-y-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">All Timeframes Overview</h3>
        <p className="text-sm text-muted-foreground">
          Summary of active patterns across all 9 timeframes
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {TIMEFRAMES.map(tf => {
          const tfData = snapshot.timeframes[tf];
          if (!tfData) return null;

          const { summary } = tfData;

          return (
            <Card key={tf}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{TIMEFRAME_LABELS[tf]}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {/* Total Patterns */}
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Total Patterns</span>
                    <span className="font-semibold">
                      {summary.active_fvgs_count + summary.active_lps_count + summary.active_obs_count}
                    </span>
                  </div>

                  {/* Pattern Type Breakdown */}
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">FVGs</span>
                    <span>{summary.active_fvgs_count}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Session Levels</span>
                    <span>{summary.active_lps_count}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Order Blocks</span>
                    <span>{summary.active_obs_count}</span>
                  </div>

                  {/* Bullish/Bearish */}
                  <div className="pt-2 border-t">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-green-600 dark:text-green-400">Bullish</span>
                      <span className="font-semibold text-green-600 dark:text-green-400">
                        {summary.bullish_count}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-red-600 dark:text-red-400">Bearish</span>
                      <span className="font-semibold text-red-600 dark:text-red-400">
                        {summary.bearish_count}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
