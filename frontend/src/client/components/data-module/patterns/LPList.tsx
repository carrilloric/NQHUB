import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Copy, Check } from "lucide-react";
import type { LiquidityPoolResponse } from "@/types/patterns";

interface LPListProps {
  pools: LiquidityPoolResponse[];
  totalCount?: number;
}

export const LPList: React.FC<LPListProps> = ({ pools, totalCount }) => {
  const [copied, setCopied] = React.useState(false);

  // Sort pools by start_time for numbering
  const sortedPools = React.useMemo(() => {
    return [...pools].sort((a, b) => {
      const timeA = a.start_time || a.formation_time;
      const timeB = b.start_time || b.formation_time;
      return new Date(timeA).getTime() - new Date(timeB).getTime();
    });
  }, [pools]);

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

  const formatTimeOnly = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  const formatTimeWithDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const dateStr = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
    const timeStr = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
    return `${dateStr} ${timeStr}`;
  };

  const getPoolTypeBadge = (poolType: string) => {
    const variants: Record<string, string> = {
      EQH: "bg-blue-500 text-white",
      EQL: "bg-blue-500 text-white",
      ASH: "bg-purple-500 text-white",
      ASL: "bg-purple-500 text-white",
      LSH: "bg-green-500 text-white",
      LSL: "bg-green-500 text-white",
      NYH: "bg-orange-500 text-white",
      NYL: "bg-orange-500 text-white",
    };
    return variants[poolType] || "bg-gray-500 text-white";
  };

  const getStrengthBadge = (strength: string) => {
    const variants: Record<string, string> = {
      STRONG: "bg-green-500 text-white",
      NORMAL: "bg-yellow-500 text-black",
      WEAK: "bg-gray-500 text-white",
    };
    return variants[strength] || "bg-gray-300";
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      UNMITIGATED: "bg-green-500 text-white",
      RESPECTED: "bg-blue-500 text-white",
      SWEPT: "bg-orange-500 text-white",
      MITIGATED: "bg-red-500 text-white",
    };
    return variants[status] || "bg-gray-300";
  };

  // Generate ATAS-friendly text format for EQH/EQL pools as rectangles
  const generateATASFormat = () => {
    let text = "#\tTIME_RANGE\t\t\t\tTYPE\tLIQUIDITY\t\tRECTANGLE_ZONE\t\t\tTOUCHES\n";
    text += "=".repeat(120) + "\n";

    sortedPools.forEach((pool, index) => {
      let timeRange = "";
      if (pool.start_time && pool.end_time) {
        const start = formatTimeWithDate(pool.start_time);
        const end = formatTimeWithDate(pool.end_time);
        timeRange = `${start} to ${end} EST`;
      } else {
        const date = new Date(pool.formation_time);
        const dateStr = date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        });
        const timeStr = date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });
        timeRange = `${dateStr} ${timeStr} EST`;
      }

      const liquidity = pool.liquidity_type || "-";

      let zone = "";
      if (pool.zone_low !== undefined && pool.zone_high !== undefined) {
        const size = pool.zone_size ? pool.zone_size.toFixed(1) : (pool.zone_high - pool.zone_low).toFixed(1);
        zone = `H:${pool.zone_high.toFixed(2)} L:${pool.zone_low.toFixed(2)} (${size}pts)`;
      } else {
        zone = pool.level.toFixed(2);
      }

      text += `${index + 1}\t${timeRange}\t${pool.pool_type}\t${liquidity}\t${zone}\t${pool.num_touches}\n`;
    });

    return text;
  };

  const handleCopyATAS = async () => {
    try {
      await navigator.clipboard.writeText(generateATASFormat());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text:", err);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle>Liquidity Pool List</CardTitle>
          <CardDescription>
            Showing {pools.length} {totalCount !== undefined && `of ${totalCount}`} Liquidity Pools
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopyATAS}
          className="ml-2"
        >
          {copied ? (
            <>
              <Check className="mr-2 h-4 w-4" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="mr-2 h-4 w-4" />
              Copy for ATAS
            </>
          )}
        </Button>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-center p-2">#</th>
                <th className="text-left p-2">Time Range</th>
                <th className="text-left p-2">Type / Liquidity</th>
                <th className="text-right p-2">Rectangle Zone</th>
                <th className="text-center p-2">Touches</th>
                <th className="text-right p-2">Volume</th>
                <th className="text-left p-2">Strength</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {sortedPools.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center p-4 text-muted-foreground">
                    No Liquidity Pools match the selected filters
                  </td>
                </tr>
              ) : (
                sortedPools.map((pool, index) => (
                  <tr
                    key={pool.lp_id}
                    className="border-b hover:bg-muted/50 transition-colors"
                  >
                    <td className="p-2 text-center font-mono font-semibold text-xs">
                      {index + 1}
                    </td>
                    <td className="p-2 font-mono text-xs">
                      {pool.start_time && pool.end_time ? (
                        <div>
                          <div>{formatTimeWithDate(pool.start_time)} EST</div>
                          <div className="text-muted-foreground text-[10px]">
                            to {formatTimeWithDate(pool.end_time)} EST
                          </div>
                        </div>
                      ) : (
                        <div>{formatTime(pool.formation_time)}</div>
                      )}
                    </td>
                    <td className="p-2">
                      <div className="flex flex-col gap-1">
                        <Badge className={`text-xs ${getPoolTypeBadge(pool.pool_type)}`}>
                          {pool.pool_type}
                        </Badge>
                        {pool.liquidity_type && (
                          <span className="text-[10px] text-muted-foreground">
                            {pool.liquidity_type}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="p-2 text-right">
                      {pool.zone_low !== undefined && pool.zone_high !== undefined ? (
                        // LP with zone (EQH/EQL) - Rectangle
                        <div className="font-mono text-xs">
                          <div className="font-semibold">
                            {pool.zone_high.toFixed(2)} (High)
                          </div>
                          <div className="text-muted-foreground text-[10px]">
                            {pool.zone_low.toFixed(2)} (Low)
                          </div>
                          <div className="text-blue-500 text-[10px] font-semibold">
                            {pool.zone_size ? `${pool.zone_size.toFixed(1)} pts` : ''}
                          </div>
                        </div>
                      ) : (
                        // Session level (point)
                        <div className="font-semibold">{pool.level.toFixed(2)}</div>
                      )}
                    </td>
                    <td className="p-2 text-center font-mono">
                      {pool.num_touches}
                      {pool.num_touches >= 3 && <span className="ml-1">⭐</span>}
                    </td>
                    <td className="p-2 text-right font-mono text-xs">
                      {pool.total_volume !== null
                        ? pool.total_volume.toLocaleString()
                        : "N/A"}
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getStrengthBadge(pool.strength)}`}>
                        {pool.strength}
                      </Badge>
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getStatusBadge(pool.status)}`}>
                        {pool.status}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* ATAS Format Preview */}
        {pools.length > 0 && (
          <div className="mt-4 p-3 bg-muted/50 rounded-md font-mono text-xs">
            <p className="text-muted-foreground mb-2">ATAS Format Preview:</p>
            <pre className="whitespace-pre overflow-x-auto">{generateATASFormat()}</pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
