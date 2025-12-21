import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { FVGResponse } from "@/types/patterns";

interface FVGListProps {
  fvgs: FVGResponse[];
  totalCount?: number;
}

export const FVGList: React.FC<FVGListProps> = ({ fvgs, totalCount }) => {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const getSignificanceBadge = (significance: string) => {
    const variants: Record<string, string> = {
      EXTREME: "bg-purple-500 text-white",
      LARGE: "bg-red-500 text-white",
      MEDIUM: "bg-orange-500 text-white",
      SMALL: "bg-yellow-500 text-black",
      MICRO: "bg-gray-500 text-white",
    };
    return variants[significance] || "bg-gray-300";
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      UNMITIGATED: "bg-green-500 text-white",
      REDELIVERED: "bg-yellow-500 text-black",
      REBALANCED: "bg-red-500 text-white",
    };
    return variants[status] || "bg-gray-300";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>FVG List</CardTitle>
        <CardDescription>
          Showing {fvgs.length} {totalCount !== undefined && `of ${totalCount}`} FVGs
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Type</th>
                <th className="text-right p-2">Gap (pts)</th>
                <th className="text-left p-2">Significance</th>
                <th className="text-right p-2">Disp. Score</th>
                <th className="text-center p-2">BOS</th>
                <th className="text-left p-2">Status</th>
                <th className="text-right p-2">Range</th>
              </tr>
            </thead>
            <tbody>
              {fvgs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center p-4 text-muted-foreground">
                    No FVGs match the selected filters
                  </td>
                </tr>
              ) : (
                fvgs.map((fvg) => (
                  <tr
                    key={fvg.fvg_id}
                    className="border-b hover:bg-muted/50 transition-colors"
                  >
                    <td className="p-2 font-mono text-xs">
                      {formatTime(fvg.formation_time)}
                    </td>
                    <td className="p-2">
                      <Badge
                        variant={fvg.fvg_type === "BULLISH" ? "default" : "destructive"}
                        className="text-xs"
                      >
                        {fvg.fvg_type === "BULLISH" ? "🟢 BULL" : "🔴 BEAR"}
                      </Badge>
                    </td>
                    <td className="p-2 text-right font-semibold">
                      {fvg.gap_size.toFixed(2)}
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getSignificanceBadge(fvg.significance)}`}>
                        {fvg.significance}
                      </Badge>
                    </td>
                    <td className="p-2 text-right font-mono">
                      {fvg.displacement_score !== undefined
                        ? `${fvg.displacement_score.toFixed(2)}x`
                        : "N/A"}
                    </td>
                    <td className="p-2 text-center text-lg">
                      {fvg.has_break_of_structure ? "⚡" : "-"}
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getStatusBadge(fvg.status)}`}>
                        {fvg.status}
                      </Badge>
                    </td>
                    <td className="p-2 text-right font-mono text-xs">
                      {fvg.fvg_start.toFixed(2)} - {fvg.fvg_end.toFixed(2)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};
