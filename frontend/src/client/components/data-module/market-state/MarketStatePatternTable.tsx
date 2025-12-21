/**
 * Market State Pattern Table
 *
 * Displays active patterns (FVGs, Session Levels, OBs) in tables
 */
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { FVGResponse, LiquidityPoolResponse, OrderBlockResponse } from "@/types/patterns";

interface MarketStatePatternTableProps {
  fvgs: FVGResponse[];
  sessionLevels: LiquidityPoolResponse[];
  orderBlocks: OrderBlockResponse[];
}

export const MarketStatePatternTable: React.FC<MarketStatePatternTableProps> = ({
  fvgs,
  sessionLevels,
  orderBlocks
}) => {
  return (
    <div className="space-y-6">
      {/* Fair Value Gaps Table */}
      {fvgs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Fair Value Gaps ({fvgs.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Formation Time</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Gap Start</TableHead>
                    <TableHead>Gap End</TableHead>
                    <TableHead>Gap Size</TableHead>
                    <TableHead>Significance</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fvgs.map((fvg) => (
                    <TableRow key={fvg.fvg_id}>
                      <TableCell>{fvg.fvg_id}</TableCell>
                      <TableCell className="whitespace-nowrap">
                        {new Date(fvg.formation_time).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <span className={
                          fvg.fvg_type === "BULLISH"
                            ? "text-green-600 dark:text-green-400 font-semibold"
                            : "text-red-600 dark:text-red-400 font-semibold"
                        }>
                          {fvg.fvg_type}
                        </span>
                      </TableCell>
                      <TableCell>{fvg.fvg_start.toFixed(2)}</TableCell>
                      <TableCell>{fvg.fvg_end.toFixed(2)}</TableCell>
                      <TableCell>{fvg.gap_size.toFixed(2)}</TableCell>
                      <TableCell>{fvg.significance}</TableCell>
                      <TableCell>
                        <span className="px-2 py-1 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs">
                          {fvg.status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Levels Table */}
      {sessionLevels.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Session Levels ({sessionLevels.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Formation Time</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Level</TableHead>
                    <TableHead>Touches</TableHead>
                    <TableHead>Strength</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessionLevels.map((lp) => (
                    <TableRow key={lp.lp_id}>
                      <TableCell>{lp.lp_id}</TableCell>
                      <TableCell className="whitespace-nowrap">
                        {new Date(lp.formation_time).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <span className="font-semibold">{lp.pool_type}</span>
                      </TableCell>
                      <TableCell>{lp.level.toFixed(2)}</TableCell>
                      <TableCell>{lp.num_touches}</TableCell>
                      <TableCell>
                        <span className={
                          lp.strength === "STRONG"
                            ? "text-green-600 dark:text-green-400 font-semibold"
                            : lp.strength === "WEAK"
                            ? "text-yellow-600 dark:text-yellow-400"
                            : ""
                        }>
                          {lp.strength}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="px-2 py-1 rounded-md bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-xs">
                          {lp.status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Order Blocks Table */}
      {orderBlocks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Order Blocks ({orderBlocks.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Formation Time</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>High</TableHead>
                    <TableHead>Low</TableHead>
                    <TableHead>Impulse</TableHead>
                    <TableHead>Quality</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orderBlocks.map((ob) => (
                    <TableRow key={ob.ob_id}>
                      <TableCell>{ob.ob_id}</TableCell>
                      <TableCell className="whitespace-nowrap">
                        {new Date(ob.formation_time).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <span className={
                          ob.ob_type.includes("BULLISH")
                            ? "text-green-600 dark:text-green-400 font-semibold"
                            : "text-red-600 dark:text-red-400 font-semibold"
                        }>
                          {ob.ob_type}
                        </span>
                      </TableCell>
                      <TableCell>{ob.ob_high.toFixed(2)}</TableCell>
                      <TableCell>{ob.ob_low.toFixed(2)}</TableCell>
                      <TableCell>{ob.impulse_move.toFixed(2)}</TableCell>
                      <TableCell>
                        <span className={
                          ob.quality === "HIGH"
                            ? "text-green-600 dark:text-green-400 font-semibold"
                            : ob.quality === "LOW"
                            ? "text-yellow-600 dark:text-yellow-400"
                            : ""
                        }>
                          {ob.quality}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="px-2 py-1 rounded-md bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs">
                          {ob.status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {fvgs.length === 0 && sessionLevels.length === 0 && orderBlocks.length === 0 && (
        <Card>
          <CardContent className="text-center py-12 text-muted-foreground">
            <p>No active patterns for this timeframe</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
