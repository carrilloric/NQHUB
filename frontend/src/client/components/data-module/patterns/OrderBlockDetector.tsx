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
import type { OrderBlockGenerationResponse } from "@/types/patterns";

export const OrderBlockDetector: React.FC = () => {
  const [symbol, setSymbol] = useState("NQZ5");
  const [startDate, setStartDate] = useState("2025-11-24");
  const [endDate, setEndDate] = useState("2025-11-24");
  const [timeframe, setTimeframe] = useState("5min");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OrderBlockGenerationResponse | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.generateOrderBlocks({
        symbol,
        start_date: startDate,
        end_date: endDate,
        timeframe,
      });
      setResult(response);
    } catch (err) {
      console.error("Error generating Order Blocks:", err);
      setError(ApiClient.getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Order Block Detection</CardTitle>
          <CardDescription>
            Detect Bullish and Bearish Order Blocks based on impulse movements
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="ob-symbol">Symbol</Label>
              <Input
                id="ob-symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="NQZ5"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ob-timeframe">Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger id="ob-timeframe">
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
              <Label htmlFor="ob-start-date">Start Date</Label>
              <Input
                id="ob-start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ob-end-date">End Date</Label>
              <Input
                id="ob-end-date"
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
                Detecting Order Blocks...
              </>
            ) : (
              "Generate Order Blocks"
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
                  <p className="text-sm text-muted-foreground">Total Order Blocks</p>
                  <p className="text-2xl font-bold">{result.total}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Min Impulse (Auto)</p>
                  <p className="text-2xl font-bold">{result.auto_parameters.min_impulse.toFixed(1)} pts</p>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Breakdown by Type</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(result.breakdown).map(([type, count]) => (
                    <div key={type} className="flex justify-between border-b pb-1">
                      <span className={type.includes("BULLISH") ? "text-green-500" : "text-red-500"}>
                        {type}:
                      </span>
                      <span className="font-semibold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <PatternReport report={result.text_report} title="Order Block Detection Report" />
        </>
      )}
    </div>
  );
};
