import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { OrderBlockResponse } from "@/types/patterns";

interface OBListProps {
  orderBlocks: OrderBlockResponse[];
  totalCount?: number;
}

export const OBList: React.FC<OBListProps> = ({ orderBlocks, totalCount }) => {
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

  const getOBTypeBadge = (obType: string) => {
    if (obType === "BULLISH OB") {
      return "bg-green-500 text-white";
    } else if (obType === "BEARISH OB") {
      return "bg-red-500 text-white";
    } else if (obType === "STRONG BULLISH OB") {
      return "bg-green-600 text-white";
    } else if (obType === "STRONG BEARISH OB") {
      return "bg-red-600 text-white";
    }
    return "bg-gray-500 text-white";
  };

  const getOBTypeLabel = (obType: string) => {
    if (obType === "BULLISH OB") return "🟢 BULL OB";
    if (obType === "BEARISH OB") return "🔴 BEAR OB";
    if (obType === "STRONG BULLISH OB") return "⚡🟢 STRONG BULL";
    if (obType === "STRONG BEARISH OB") return "⚡🔴 STRONG BEAR";
    return obType;
  };

  const getQualityBadge = (quality: string) => {
    const variants: Record<string, string> = {
      HIGH: "bg-purple-500 text-white",
      MEDIUM: "bg-orange-500 text-white",
      LOW: "bg-gray-500 text-white",
    };
    return variants[quality] || "bg-gray-300";
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      ACTIVE: "bg-green-500 text-white",
      TESTED: "bg-yellow-500 text-black",
      BROKEN: "bg-red-500 text-white",
    };
    return variants[status] || "bg-gray-300";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Order Block List</CardTitle>
        <CardDescription>
          Showing {orderBlocks.length} {totalCount !== undefined && `of ${totalCount}`} Order Blocks
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Type</th>
                <th className="text-right p-2">Range</th>
                <th className="text-right p-2">Size</th>
                <th className="text-right p-2">Impulse</th>
                <th className="text-right p-2">Volume</th>
                <th className="text-left p-2">Quality</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {orderBlocks.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center p-4 text-muted-foreground">
                    No Order Blocks match the selected filters
                  </td>
                </tr>
              ) : (
                orderBlocks.map((ob) => (
                  <tr
                    key={ob.ob_id}
                    className="border-b hover:bg-muted/50 transition-colors"
                  >
                    <td className="p-2 font-mono text-xs">
                      {formatTime(ob.formation_time)}
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getOBTypeBadge(ob.ob_type)}`}>
                        {getOBTypeLabel(ob.ob_type)}
                      </Badge>
                    </td>
                    <td className="p-2 text-right font-mono text-xs">
                      {ob.ob_low.toFixed(2)} - {ob.ob_high.toFixed(2)}
                    </td>
                    <td className="p-2 text-right font-semibold">
                      {(ob.ob_high - ob.ob_low).toFixed(2)} pts
                    </td>
                    <td className="p-2 text-right font-mono">
                      {ob.impulse_move.toFixed(1)} pts
                      {ob.impulse_direction === "UP" ? " ↑" : " ↓"}
                    </td>
                    <td className="p-2 text-right font-mono text-xs">
                      {ob.ob_volume.toLocaleString()}
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getQualityBadge(ob.quality)}`}>
                        {ob.quality}
                      </Badge>
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getStatusBadge(ob.status)}`}>
                        {ob.status}
                      </Badge>
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
