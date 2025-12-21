import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Copy, Check } from "lucide-react";
import type { LiquidityPoolResponse } from "@/types/patterns";

interface SessionLevelListProps {
  sessionLevels: LiquidityPoolResponse[];
  totalCount?: number;
}

export const SessionLevelList: React.FC<SessionLevelListProps> = ({ sessionLevels, totalCount }) => {
  const [copied, setCopied] = React.useState(false);

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

  const getSessionBadge = (sessionType: string) => {
    const variants: Record<string, string> = {
      ASH: "bg-purple-600 text-white",
      ASL: "bg-purple-400 text-white",
      LSH: "bg-green-600 text-white",
      LSL: "bg-green-400 text-white",
      NYH: "bg-orange-600 text-white",
      NYL: "bg-orange-400 text-white",
    };
    return variants[sessionType] || "bg-gray-500 text-white";
  };

  const getSessionName = (sessionType: string) => {
    const names: Record<string, string> = {
      ASH: "Asian Session High",
      ASL: "Asian Session Low",
      LSH: "London Session High",
      LSL: "London Session Low",
      NYH: "NY Session High",
      NYL: "NY Session Low",
    };
    return names[sessionType] || sessionType;
  };

  // Generate ATAS-friendly text format
  const generateATASFormat = () => {
    let text = "TIME\t\tTYPE\tLEVEL\n";
    text += "========================================\n";

    sessionLevels.forEach((level) => {
      const time = new Date(level.formation_time).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
      text += `${time} EST\t${level.pool_type}\t${level.level.toFixed(2)}\n`;
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
          <CardTitle>Session Levels</CardTitle>
          <CardDescription>
            Showing {sessionLevels.length} {totalCount !== undefined && `of ${totalCount}`} Session Levels
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
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Session</th>
                <th className="text-right p-2">Level</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {sessionLevels.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center p-4 text-muted-foreground">
                    No Session Levels detected for this date
                  </td>
                </tr>
              ) : (
                sessionLevels.map((level) => (
                  <tr
                    key={level.lp_id}
                    className="border-b hover:bg-muted/50 transition-colors"
                  >
                    <td className="p-2 font-mono text-xs">
                      {formatTime(level.formation_time)}
                    </td>
                    <td className="p-2">
                      <Badge className={`text-xs ${getSessionBadge(level.pool_type)}`}>
                        {level.pool_type}
                      </Badge>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {getSessionName(level.pool_type)}
                      </span>
                    </td>
                    <td className="p-2 text-right font-bold text-lg">
                      {level.level.toFixed(2)}
                    </td>
                    <td className="p-2">
                      <Badge className="text-xs bg-green-500 text-white">
                        {level.status}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* ATAS Format Preview */}
        {sessionLevels.length > 0 && (
          <div className="mt-4 p-3 bg-muted/50 rounded-md font-mono text-xs">
            <p className="text-muted-foreground mb-2">ATAS Format Preview:</p>
            <pre className="whitespace-pre">{generateATASFormat()}</pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
