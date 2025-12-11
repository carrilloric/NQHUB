import React, { useState } from "react";
import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DatePicker } from "@/components/ui/date-picker";
import { CheckCircle, XCircle, AlertTriangle, Loader2 } from "lucide-react";
import type {
  IntegrityCheckResponse,
  SymbolsList,
  IntegrityTimeframeRow,
  IntegrityRelationRow,
} from "@/types/etl";
import {
  INTEGRITY_STATUS_COLORS,
  INTEGRITY_STATUS_BG_COLORS,
} from "@/types/etl";

export const IntegrityCheck: React.FC = () => {
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("all");
  const [symbols, setSymbols] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingSymbols, setLoadingSymbols] = useState(false);
  const [result, setResult] = useState<IntegrityCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch symbols on mount
  React.useEffect(() => {
    const fetchSymbols = async () => {
      setLoadingSymbols(true);
      try {
        const response = await fetch("/api/v1/etl/symbols/list");
        if (response.ok) {
          const data: SymbolsList = await response.json();
          setSymbols(data.symbols);
        }
      } catch (err) {
        console.error("Error fetching symbols:", err);
      } finally {
        setLoadingSymbols(false);
      }
    };
    fetchSymbols();
  }, []);

  const handleCheck = async () => {
    if (!startDate || !endDate) {
      setError("Please select both start and end dates");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        start_date: format(startDate, "yyyy-MM-dd"),
        end_date: format(endDate, "yyyy-MM-dd"),
      });
      if (selectedSymbol && selectedSymbol !== "all") {
        params.append("symbol", selectedSymbol);
      }

      const response = await fetch(`/api/v1/etl/integrity?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: IntegrityCheckResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(`Error checking integrity: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "ok":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case "mismatch":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div className="space-y-4">
      {/* Control Panel - Sticky */}
      <Card className="sticky top-0 z-10 bg-card">
        <CardHeader>
          <CardTitle className="text-base">Integrity Check Parameters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <DatePicker
                date={startDate}
                onDateChange={setStartDate}
                placeholder="Select start date"
              />
            </div>
            <div className="space-y-2">
              <Label>End Date</Label>
              <DatePicker
                date={endDate}
                onDateChange={setEndDate}
                placeholder="Select end date"
              />
            </div>
            <div>
              <Label htmlFor="symbol">Symbol (Optional)</Label>
              <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                <SelectTrigger id="symbol">
                  <SelectValue placeholder="All symbols" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Symbols</SelectItem>
                  {symbols.map((sym) => (
                    <SelectItem key={sym} value={sym}>
                      {sym}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Button onClick={handleCheck} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Checking...
                  </>
                ) : (
                  "Check Integrity"
                )}
              </Button>
            </div>
          </div>
          {error && (
            <p className="text-red-500 text-sm mt-2">{error}</p>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <>
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                Overall Status:
                <span className={INTEGRITY_STATUS_COLORS[result.overall_status]}>
                  {result.overall_status.toUpperCase()}
                </span>
                {getStatusIcon(result.overall_status === "errors" ? "mismatch" : result.overall_status === "warnings" ? "warning" : "ok")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center p-3 bg-green-500/20 border border-green-500/30 rounded">
                  <div className="text-2xl font-bold text-green-500">{result.summary.ok}</div>
                  <div className="text-muted-foreground">OK</div>
                </div>
                <div className="text-center p-3 bg-yellow-500/20 border border-yellow-500/30 rounded">
                  <div className="text-2xl font-bold text-yellow-500">{result.summary.warning}</div>
                  <div className="text-muted-foreground">Warnings</div>
                </div>
                <div className="text-center p-3 bg-red-500/20 border border-red-500/30 rounded">
                  <div className="text-2xl font-bold text-red-500">{result.summary.mismatch}</div>
                  <div className="text-muted-foreground">Mismatches</div>
                </div>
              </div>
              <div className="mt-4 text-sm text-muted-foreground">
                <p>Period: {result.start_date} to {result.end_date}</p>
                <p>Total Trading Minutes: {formatNumber(result.total_trading_minutes)}</p>
                {result.symbol && <p>Symbol: {result.symbol}</p>}
              </div>
            </CardContent>
          </Card>

          {/* Timeframe Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Timeframe Comparison</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="rounded-md border border-border overflow-hidden">
                <Table>
                  <TableHeader className="bg-muted/50">
                    <TableRow className="hover:bg-muted/50 border-border">
                      <TableHead className="text-foreground">Timeframe</TableHead>
                      <TableHead className="text-right text-foreground">Expected</TableHead>
                      <TableHead className="text-right text-foreground">Actual</TableHead>
                      <TableHead className="text-right text-foreground">Diff</TableHead>
                      <TableHead className="text-center text-foreground">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.timeframe_checks.map((row: IntegrityTimeframeRow) => (
                      <TableRow key={row.timeframe} className={`${INTEGRITY_STATUS_BG_COLORS[row.status]} border-border`}>
                        <TableCell className="font-medium">{row.timeframe}</TableCell>
                        <TableCell className="text-right">{formatNumber(row.expected)}</TableCell>
                        <TableCell className="text-right">{formatNumber(row.actual)}</TableCell>
                        <TableCell className={`text-right ${row.diff >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                          {row.diff >= 0 ? '+' : ''}{formatNumber(row.diff)}
                        </TableCell>
                        <TableCell className="text-center">
                          {getStatusIcon(row.status)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Relation Check Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Timeframe Relations</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="rounded-md border border-border overflow-hidden">
                <Table>
                  <TableHeader className="bg-muted/50">
                    <TableRow className="hover:bg-muted/50 border-border">
                      <TableHead className="text-foreground">Relation</TableHead>
                      <TableHead className="text-right text-foreground">Expected Ratio</TableHead>
                      <TableHead className="text-right text-foreground">Actual Ratio</TableHead>
                      <TableHead className="text-center text-foreground">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.relation_checks.map((row: IntegrityRelationRow) => (
                      <TableRow key={row.relation} className={`${INTEGRITY_STATUS_BG_COLORS[row.status]} border-border`}>
                        <TableCell className="font-medium">{row.relation}</TableCell>
                        <TableCell className="text-right">{row.expected_ratio.toFixed(1)}</TableCell>
                        <TableCell className="text-right">{row.actual_ratio.toFixed(2)}</TableCell>
                        <TableCell className="text-center">
                          {getStatusIcon(row.status)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
