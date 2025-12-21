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
import { FVGList } from "./FVGList";
import type { FVGGenerationResponse } from "@/types/patterns";

export const FVGDetector: React.FC = () => {
  // Detection parameters
  const [symbol, setSymbol] = useState("NQZ5");
  const [startDate, setStartDate] = useState<Date | undefined>(new Date(2025, 10, 24)); // Nov 24, 2025
  const [endDate, setEndDate] = useState<Date | undefined>(new Date(2025, 10, 24));
  const [timeframe, setTimeframe] = useState("5min");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FVGGenerationResponse | null>(null);

  // Filter states
  const [showAll, setShowAll] = useState(true);
  const [selectedSignificance, setSelectedSignificance] = useState<string[]>([]);
  const [minDisplacement, setMinDisplacement] = useState(0);
  const [maxDisplacement, setMaxDisplacement] = useState(5);
  const [onlyBOS, setOnlyBOS] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.generateFVGs({
        symbol,
        start_date: formatDateForAPI(startDate),
        end_date: formatDateForAPI(endDate),
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

  // Filter logic
  const filteredFVGs = useMemo(() => {
    if (!result) return [];
    if (showAll) return result.fvgs;

    return result.fvgs.filter((fvg) => {
      // Filter by significance
      if (selectedSignificance.length > 0 && !selectedSignificance.includes(fvg.significance)) {
        return false;
      }

      // Filter by displacement score
      if (fvg.displacement_score !== undefined) {
        if (fvg.displacement_score < minDisplacement || fvg.displacement_score > maxDisplacement) {
          return false;
        }
      }

      // Filter by BOS
      if (onlyBOS && !fvg.has_break_of_structure) {
        return false;
      }

      return true;
    });
  }, [result, showAll, selectedSignificance, minDisplacement, maxDisplacement, onlyBOS]);

  // Toggle significance selection
  const toggleSignificance = (sig: string) => {
    setSelectedSignificance((prev) =>
      prev.includes(sig) ? prev.filter((s) => s !== sig) : [...prev, sig]
    );
  };

  // Date conversion helpers
  const formatDateForAPI = (date: Date | undefined): string => {
    if (!date) return "";
    return format(date, "yyyy-MM-dd");
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
              <DatePicker
                date={startDate}
                onDateChange={setStartDate}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date">End Date</Label>
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
          {/* Detection Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Detection Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total FVGs</p>
                  <p className="text-2xl font-bold">{result.total}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Showing</p>
                  <p className="text-2xl font-bold text-primary">{filteredFVGs.length}</p>
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

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Filters</CardTitle>
              <CardDescription>
                Filter FVGs by significance, displacement score, and break of structure
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Show All Toggle */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-all"
                  checked={showAll}
                  onCheckedChange={(checked) => setShowAll(checked as boolean)}
                />
                <Label htmlFor="show-all" className="font-semibold">
                  Show All FVGs (disable filters)
                </Label>
              </div>

              <div className={showAll ? "opacity-50 pointer-events-none" : ""}>
                {/* Significance Filter */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Significance</Label>
                  <div className="flex flex-wrap gap-2">
                    {["EXTREME", "LARGE", "MEDIUM", "SMALL", "MICRO"].map((sig) => (
                      <div key={sig} className="flex items-center space-x-2">
                        <Checkbox
                          id={`sig-${sig}`}
                          checked={selectedSignificance.includes(sig)}
                          onCheckedChange={() => toggleSignificance(sig)}
                        />
                        <Label htmlFor={`sig-${sig}`} className="text-sm cursor-pointer">
                          {sig}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Displacement Score Filter */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Displacement Score: {minDisplacement.toFixed(1)}x - {maxDisplacement.toFixed(1)}x
                  </Label>
                  <div className="px-2">
                    <Slider
                      min={0}
                      max={5}
                      step={0.1}
                      value={[minDisplacement, maxDisplacement]}
                      onValueChange={([min, max]) => {
                        setMinDisplacement(min);
                        setMaxDisplacement(max);
                      }}
                      className="w-full"
                    />
                  </div>
                </div>

                {/* BOS Filter */}
                <div className="flex items-center space-x-2 mt-6">
                  <Checkbox
                    id="only-bos"
                    checked={onlyBOS}
                    onCheckedChange={(checked) => setOnlyBOS(checked as boolean)}
                  />
                  <Label htmlFor="only-bos" className="text-sm cursor-pointer">
                    Only FVGs with Break of Structure ⚡
                  </Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* FVG List */}
          <FVGList fvgs={filteredFVGs} totalCount={result.total} />

          {/* Full Report */}
          <PatternReport report={result.text_report} title="FVG Detection Report" />
        </>
      )}
    </div>
  );
};
