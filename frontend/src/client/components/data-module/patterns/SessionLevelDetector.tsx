import React, { useState, useMemo } from "react";
import { format } from "date-fns";
import { apiClient, ApiClient } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { DatePicker } from "@/components/ui/date-picker";
import { Loader2 } from "lucide-react";
import { SessionLevelList } from "./SessionLevelList";
import { PatternReport } from "./PatternReport";
import type { LiquidityPoolGenerationResponse } from "@/types/patterns";

export const SessionLevelDetector: React.FC = () => {
  // Detection parameters
  const [symbol, setSymbol] = useState("NQZ5");
  const [date, setDate] = useState<Date | undefined>(new Date(2025, 10, 24)); // Nov 24, 2025
  const [timeframe, setTimeframe] = useState("5min");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LiquidityPoolGenerationResponse | null>(null);

  // Date conversion helper
  const formatDateForAPI = (date: Date | undefined): string => {
    if (!date) return "";
    return format(date, "yyyy-MM-dd");
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Request only session level pool types
      const response = await apiClient.generateLiquidityPools({
        symbol,
        date: formatDateForAPI(date),
        timeframe,
        pool_types: ["ASH", "ASL", "LSH", "LSL", "NYH", "NYL"], // Only session levels
      });
      setResult(response);
    } catch (err) {
      console.error("Error generating Session Levels:", err);
      setError(ApiClient.getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Filter to show only session levels (defensive)
  const sessionLevels = useMemo(() => {
    if (!result) return [];
    return result.pools.filter((pool) =>
      ["ASH", "ASL", "LSH", "LSL", "NYH", "NYL"].includes(pool.pool_type)
    );
  }, [result]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Session Level Detection</CardTitle>
          <CardDescription>
            Detect key session highs and lows: Asian (ASH/ASL), London (LSH/LSL), NY (NYH/NYL)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sl-symbol">Symbol</Label>
              <Input
                id="sl-symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="NQZ5"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sl-timeframe">Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger id="sl-timeframe">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="30s">30 seconds</SelectItem>
                  <SelectItem value="1min">1 minute</SelectItem>
                  <SelectItem value="5min">5 minutes</SelectItem>
                  <SelectItem value="15min">15 minutes</SelectItem>
                  <SelectItem value="1hr">1 hour</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="sl-date">Date</Label>
              <DatePicker
                date={date}
                onDateChange={setDate}
              />
            </div>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={loading || !symbol.trim() || !date}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Detecting Session Levels...
              </>
            ) : (
              "Generate Session Levels"
            )}
          </Button>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {result && (
        <>
          {/* Detection Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Detection Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Session Levels</p>
                  <p className="text-2xl font-bold">{sessionLevels.length}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Date</p>
                  <p className="text-lg font-semibold">{formatDateForAPI(date)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Symbol</p>
                  <p className="text-lg font-semibold">{symbol}</p>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Session Breakdown</p>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  {["ASH", "ASL", "LSH", "LSL", "NYH", "NYL"].map((type) => {
                    const count = sessionLevels.filter((l) => l.pool_type === type).length;
                    return (
                      <div key={type} className="flex justify-between border-b pb-1">
                        <span className="text-muted-foreground">{type}:</span>
                        <span className="font-semibold">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Session Level List */}
          <SessionLevelList sessionLevels={sessionLevels} totalCount={sessionLevels.length} />

          {/* Full Report */}
          <PatternReport report={result.text_report} title="Session Level Detection Report" />
        </>
      )}
    </div>
  );
};
