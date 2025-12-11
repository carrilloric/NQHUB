import React, { useState } from "react";
import { apiClient, ApiClient } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";
import { PatternReport } from "./PatternReport";
import type { FVGGenerationResponse } from "@/types/patterns";

export const FVGDetector: React.FC = () => {
  const [symbol, setSymbol] = useState("NQZ5");
  const [startDate, setStartDate] = useState("2025-11-24");
  const [endDate, setEndDate] = useState("2025-11-24");
  const [timeframe, setTimeframe] = useState("5min");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FVGGenerationResponse | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.generateFVGs({
        symbol,
        start_date: startDate,
        end_date: endDate,
        timeframe,
      });
      setResult(response);
    } catch (err) {
      console.error("Error generating FVGs:", err);
      setError(ApiClient.getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Fair Value Gap Detection</CardTitle>
          <CardDescription>
            Detect bullish and bearish Fair Value Gaps with auto-calibrated parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="symbol">Symbol</Label>
              <Input
                id="symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="NQZ5"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="timeframe">Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger id="timeframe">
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
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={loading || !symbol || !startDate || !endDate}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Detecting FVGs...
              </>
            ) : (
              "Generate FVGs"
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
          <Card>
            <CardHeader>
              <CardTitle>Detection Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total FVGs</p>
                  <p className="text-2xl font-bold">{result.total}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Min Gap Size (Auto)</p>
                  <p className="text-2xl font-bold">{result.auto_parameters.min_gap_size.toFixed(2)} pts</p>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Detected Patterns</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex justify-between border-b pb-1">
                    <span className="text-green-500">Bullish:</span>
                    <span className="font-semibold">
                      {result.fvgs.filter((f) => f.fvg_type === "BULLISH").length}
                    </span>
                  </div>
                  <div className="flex justify-between border-b pb-1">
                    <span className="text-red-500">Bearish:</span>
                    <span className="font-semibold">
                      {result.fvgs.filter((f) => f.fvg_type === "BEARISH").length}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <PatternReport report={result.text_report} title="FVG Detection Report" />
        </>
      )}
    </div>
  );
};
