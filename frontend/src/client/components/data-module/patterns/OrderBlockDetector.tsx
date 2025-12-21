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
import { OBList } from "./OBList";
import type { OrderBlockGenerationResponse } from "@/types/patterns";

export const OrderBlockDetector: React.FC = () => {
  // Detection parameters
  const [symbol, setSymbol] = useState("NQZ5");
  const [startDate, setStartDate] = useState<Date | undefined>(new Date(2025, 10, 24)); // Nov 24, 2025
  const [endDate, setEndDate] = useState<Date | undefined>(new Date(2025, 10, 24));
  const [timeframe, setTimeframe] = useState("5min");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OrderBlockGenerationResponse | null>(null);

  // Filter states
  const [showAll, setShowAll] = useState(true);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [onlyStrong, setOnlyStrong] = useState(false);
  const [selectedQuality, setSelectedQuality] = useState<string[]>([]);
  const [minImpulse, setMinImpulse] = useState(0);
  const [maxImpulse, setMaxImpulse] = useState(200);
  const [selectedStatus, setSelectedStatus] = useState<string[]>([]);

  // Date conversion helper
  const formatDateForAPI = (date: Date | undefined): string => {
    if (!date) return "";
    return format(date, "yyyy-MM-dd");
  };

  // Toggle functions
  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const toggleQuality = (qual: string) => {
    setSelectedQuality((prev) =>
      prev.includes(qual) ? prev.filter((q) => q !== qual) : [...prev, qual]
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
      const response = await apiClient.generateOrderBlocks({
        symbol,
        start_date: formatDateForAPI(startDate),
        end_date: formatDateForAPI(endDate),
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

  // Filter logic
  const filteredOrderBlocks = useMemo(() => {
    if (!result) return [];
    if (showAll) return result.order_blocks;

    return result.order_blocks.filter((ob) => {
      // Filter by type
      if (selectedTypes.length > 0 && !selectedTypes.includes(ob.ob_type)) {
        return false;
      }

      // Filter by strong only
      if (onlyStrong && !ob.ob_type.includes("STRONG")) {
        return false;
      }

      // Filter by quality
      if (selectedQuality.length > 0 && !selectedQuality.includes(ob.quality)) {
        return false;
      }

      // Filter by impulse
      if (ob.impulse_move < minImpulse || ob.impulse_move > maxImpulse) {
        return false;
      }

      // Filter by status
      if (selectedStatus.length > 0 && !selectedStatus.includes(ob.status)) {
        return false;
      }

      return true;
    });
  }, [result, showAll, selectedTypes, onlyStrong, selectedQuality, minImpulse, maxImpulse, selectedStatus]);

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
              <DatePicker
                date={startDate}
                onDateChange={setStartDate}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ob-end-date">End Date</Label>
              <DatePicker
                date={endDate}
                onDateChange={setEndDate}
              />
            </div>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={loading || !symbol.trim() || !startDate || !endDate}
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
          {/* Detection Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Detection Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Order Blocks</p>
                  <p className="text-2xl font-bold">{result.total}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Showing</p>
                  <p className="text-2xl font-bold text-primary">{filteredOrderBlocks.length}</p>
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

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Filters</CardTitle>
              <CardDescription>
                Filter Order Blocks by type, quality, impulse, and status
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Show All Toggle */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-all-ob"
                  checked={showAll}
                  onCheckedChange={(checked) => setShowAll(checked as boolean)}
                />
                <Label htmlFor="show-all-ob" className="font-semibold">
                  Show All Order Blocks (disable filters)
                </Label>
              </div>

              <div className={showAll ? "opacity-50 pointer-events-none" : ""}>
                {/* Type Filter */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Order Block Type</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {["BULLISH OB", "BEARISH OB", "STRONG BULLISH OB", "STRONG BEARISH OB"].map((type) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          id={`ob-type-${type}`}
                          checked={selectedTypes.includes(type)}
                          onCheckedChange={() => toggleType(type)}
                        />
                        <Label htmlFor={`ob-type-${type}`} className="text-sm cursor-pointer">
                          {type}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Only Strong OBs */}
                <div className="flex items-center space-x-2 mt-6">
                  <Checkbox
                    id="only-strong"
                    checked={onlyStrong}
                    onCheckedChange={(checked) => setOnlyStrong(checked as boolean)}
                  />
                  <Label htmlFor="only-strong" className="text-sm cursor-pointer">
                    Only Strong Order Blocks ⚡
                  </Label>
                </div>

                {/* Quality Filter */}
                <div className="space-y-2 mt-4">
                  <Label className="text-sm font-medium">Quality</Label>
                  <div className="flex gap-4">
                    {["HIGH", "MEDIUM", "LOW"].map((qual) => (
                      <div key={qual} className="flex items-center space-x-2">
                        <Checkbox
                          id={`quality-${qual}`}
                          checked={selectedQuality.includes(qual)}
                          onCheckedChange={() => toggleQuality(qual)}
                        />
                        <Label htmlFor={`quality-${qual}`} className="text-sm cursor-pointer">
                          {qual}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Impulse Range Slider */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Impulse Move: {minImpulse.toFixed(0)} - {maxImpulse.toFixed(0)} pts
                  </Label>
                  <div className="px-2">
                    <Slider
                      min={0}
                      max={200}
                      step={5}
                      value={[minImpulse, maxImpulse]}
                      onValueChange={([min, max]) => {
                        setMinImpulse(min);
                        setMaxImpulse(max);
                      }}
                      className="w-full"
                    />
                  </div>
                </div>

                {/* Status Filter */}
                <div className="space-y-2 mt-6">
                  <Label className="text-sm font-medium">Status</Label>
                  <div className="flex gap-4">
                    {["ACTIVE", "TESTED", "BROKEN"].map((status) => (
                      <div key={status} className="flex items-center space-x-2">
                        <Checkbox
                          id={`ob-status-${status}`}
                          checked={selectedStatus.includes(status)}
                          onCheckedChange={() => toggleStatus(status)}
                        />
                        <Label htmlFor={`ob-status-${status}`} className="text-sm cursor-pointer">
                          {status}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Order Block List */}
          <OBList orderBlocks={filteredOrderBlocks} totalCount={result.total} />

          {/* Full Report */}
          <PatternReport report={result.text_report} title="Order Block Detection Report" />
        </>
      )}
    </div>
  );
};
