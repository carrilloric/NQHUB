import React, { useState, useMemo } from "react";
import { format } from "date-fns";
import { apiClient, ApiClient } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { DatePicker } from "@/components/ui/date-picker";
import { Loader2 } from "lucide-react";
import { PatternReport } from "./PatternReport";
import { LPList } from "./LPList";
import type { LiquidityPoolGenerationResponse } from "@/types/patterns";

export const LiquidityPoolDetector: React.FC = () => {
  // Detection parameters
  const [symbol, setSymbol] = useState("NQZ5");
  const [date, setDate] = useState<Date | undefined>(new Date(2025, 10, 24)); // Nov 24, 2025
  const [timeframe, setTimeframe] = useState("5min");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LiquidityPoolGenerationResponse | null>(null);

  // Filter states
  const [showAll, setShowAll] = useState(true);
  const [selectedPoolTypes, setSelectedPoolTypes] = useState<string[]>([]);
  const [selectedStrength, setSelectedStrength] = useState<string[]>([]);
  const [minTouches, setMinTouches] = useState(2);
  const [selectedStatus, setSelectedStatus] = useState<string[]>([]);

  // Date conversion helper
  const formatDateForAPI = (date: Date | undefined): string => {
    if (!date) return "";
    return format(date, "yyyy-MM-dd");
  };

  // Toggle functions
  const togglePoolType = (type: string) => {
    setSelectedPoolTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const toggleStrength = (str: string) => {
    setSelectedStrength((prev) =>
      prev.includes(str) ? prev.filter((s) => s !== str) : [...prev, str]
    );
  };

  const toggleStatus = (st: string) => {
    setSelectedStatus((prev) =>
      prev.includes(st) ? prev.filter((s) => s !== st) : [...prev, st]
    );
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Request only EQH/EQL pool types
      const response = await apiClient.generateLiquidityPools({
        symbol,
        date: formatDateForAPI(date),
        timeframe,
        pool_types: ["EQH", "EQL"], // Only Equal Highs/Lows
      });
      setResult(response);
    } catch (err) {
      console.error("Error generating Liquidity Pools:", err);
      setError(ApiClient.getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Filter logic
  const filteredPools = useMemo(() => {
    if (!result) return [];
    if (showAll) return result.pools;

    return result.pools.filter((pool) => {
      // Filter by pool type
      if (selectedPoolTypes.length > 0 && !selectedPoolTypes.includes(pool.pool_type)) {
        return false;
      }

      // Filter by strength
      if (selectedStrength.length > 0 && !selectedStrength.includes(pool.strength)) {
        return false;
      }

      // Filter by min touches
      if (pool.num_touches < minTouches) {
        return false;
      }

      // Filter by status
      if (selectedStatus.length > 0 && !selectedStatus.includes(pool.status)) {
        return false;
      }

      return true;
    });
  }, [result, showAll, selectedPoolTypes, selectedStrength, minTouches, selectedStatus]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Liquidity Pool Detection</CardTitle>
          <CardDescription>
            Detect Equal Highs (EQH) and Equal Lows (EQL) - Zones where price repeatedly touches same levels
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="lp-symbol">Symbol</Label>
              <Input
                id="lp-symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="NQZ5"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lp-timeframe">Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger id="lp-timeframe">
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
              <Label htmlFor="lp-date">Date</Label>
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
                Detecting Liquidity Pools...
              </>
            ) : (
              "Generate Liquidity Pools"
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
                  <p className="text-sm text-muted-foreground">Total Pools</p>
                  <p className="text-2xl font-bold">{result.total}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Showing</p>
                  <p className="text-2xl font-bold text-primary">{filteredPools.length}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Tolerance</p>
                  <p className="text-2xl font-bold">±{result.auto_parameters.tolerance.toFixed(0)} pts</p>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Breakdown by Type</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(result.breakdown).map(([type, count]) => (
                    <div key={type} className="flex justify-between border-b pb-1">
                      <span className="text-muted-foreground">{type}:</span>
                      <span className="font-semibold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Filters</CardTitle>
              <CardDescription>
                Filter Liquidity Pools by type, strength, touches, and status
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Show All Toggle */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-all-lp"
                  checked={showAll}
                  onCheckedChange={(checked) => setShowAll(checked as boolean)}
                />
                <Label htmlFor="show-all-lp" className="font-semibold">
                  Show All Pools (disable filters)
                </Label>
              </div>

              <div className={showAll ? "opacity-50 pointer-events-none" : ""}>
                {/* Pool Type Filter */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Pool Type</Label>
                  <div className="flex gap-4">
                    {["EQH", "EQL"].map((type) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          id={`pool-${type}`}
                          checked={selectedPoolTypes.includes(type)}
                          onCheckedChange={() => togglePoolType(type)}
                        />
                        <Label htmlFor={`pool-${type}`} className="text-sm cursor-pointer">
                          {type}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Strength Filter */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Strength</Label>
                  <div className="flex gap-4">
                    {["STRONG", "NORMAL", "WEAK"].map((str) => (
                      <div key={str} className="flex items-center space-x-2">
                        <Checkbox
                          id={`strength-${str}`}
                          checked={selectedStrength.includes(str)}
                          onCheckedChange={() => toggleStrength(str)}
                        />
                        <Label htmlFor={`strength-${str}`} className="text-sm cursor-pointer">
                          {str}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Min Touches Slider */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Min Touches: {minTouches}
                  </Label>
                  <div className="px-2">
                    <Slider
                      min={1}
                      max={10}
                      step={1}
                      value={[minTouches]}
                      onValueChange={([val]) => setMinTouches(val)}
                      className="w-full"
                    />
                  </div>
                </div>

                {/* Status Filter */}
                <div className="space-y-2 mt-6">
                  <Label className="text-sm font-medium">Status</Label>
                  <div className="flex flex-wrap gap-2">
                    {["UNMITIGATED", "RESPECTED", "SWEPT", "MITIGATED"].map((status) => (
                      <div key={status} className="flex items-center space-x-2">
                        <Checkbox
                          id={`status-${status}`}
                          checked={selectedStatus.includes(status)}
                          onCheckedChange={() => toggleStatus(status)}
                        />
                        <Label htmlFor={`status-${status}`} className="text-sm cursor-pointer">
                          {status}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* LP List */}
          <LPList pools={filteredPools} totalCount={result.total} />

          {/* Full Report */}
          <PatternReport report={result.text_report} title="Liquidity Pool Detection Report" />
        </>
      )}
    </div>
  );
};
