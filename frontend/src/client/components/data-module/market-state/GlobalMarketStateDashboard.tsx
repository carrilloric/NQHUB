/**
 * Global Market State Dashboard
 *
 * Shows summary metrics across all timeframes
 */
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TIMEFRAMES, TIMEFRAME_SHORT_LABELS, type Timeframe } from "@/constants/timeframes";
import type { MarketStateDetailResponse } from "@/types/patterns";

interface GlobalMarketStateDashboardProps {
  snapshot: MarketStateDetailResponse;
}

export const GlobalMarketStateDashboard: React.FC<GlobalMarketStateDashboardProps> = ({
  snapshot
}) => {
  // Calculate total bullish/bearish across all timeframes
  const totalBullish = TIMEFRAMES.reduce((sum, tf) => {
    const tfData = snapshot.timeframes[tf];
    return sum + (tfData?.summary.bullish_count || 0);
  }, 0);

  const totalBearish = TIMEFRAMES.reduce((sum, tf) => {
    const tfData = snapshot.timeframes[tf];
    return sum + (tfData?.summary.bearish_count || 0);
  }, 0);

  // Calculate pattern type totals
  const totalFVGs = TIMEFRAMES.reduce((sum, tf) => {
    const tfData = snapshot.timeframes[tf];
    return sum + (tfData?.summary.active_fvgs_count || 0);
  }, 0);

  const totalSessionLevels = TIMEFRAMES.reduce((sum, tf) => {
    const tfData = snapshot.timeframes[tf];
    return sum + (tfData?.summary.active_lps_count || 0);
  }, 0);

  const totalOBs = TIMEFRAMES.reduce((sum, tf) => {
    const tfData = snapshot.timeframes[tf];
    return sum + (tfData?.summary.active_obs_count || 0);
  }, 0);

  return (
    <div className="space-y-4">
      {/* Snapshot Info */}
      <Card>
        <CardHeader>
          <CardTitle>Market State Snapshot</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Symbol</p>
              <p className="font-semibold">{snapshot.symbol}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Snapshot Time (EST)</p>
              <p className="font-semibold">{snapshot.snapshot_time_est}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Total Patterns</p>
              <p className="font-semibold">{snapshot.summary.total_patterns_all_timeframes}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Timeframes</p>
              <p className="font-semibold">{TIMEFRAMES.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Patterns
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{snapshot.summary.total_patterns_all_timeframes}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Fair Value Gaps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalFVGs}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Session Levels
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalSessionLevels}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Order Blocks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalOBs}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Bullish / Bearish
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                {totalBullish}
              </span>
              <span className="text-muted-foreground">/</span>
              <span className="text-2xl font-bold text-red-600 dark:text-red-400">
                {totalBearish}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Patterns by Timeframe */}
      <Card>
        <CardHeader>
          <CardTitle>Patterns by Timeframe</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 md:grid-cols-9 gap-4">
            {TIMEFRAMES.map(tf => (
              <div key={tf} className="text-center">
                <p className="text-xs text-muted-foreground mb-1">
                  {TIMEFRAME_SHORT_LABELS[tf]}
                </p>
                <p className="text-lg font-bold">
                  {snapshot.summary.by_timeframe[tf] || 0}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
