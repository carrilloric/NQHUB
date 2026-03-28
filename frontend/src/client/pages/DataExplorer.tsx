/**
 * Data Explorer Page
 *
 * Provides candle viewer with timeframe selector, date range picker,
 * oflow toggle, and coverage dashboard showing available data per contract/timeframe.
 */

import React, { useState } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Calendar, Download, RefreshCw, Database, ChevronDown, Eye, EyeOff } from 'lucide-react';
import { format, subDays } from 'date-fns';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { useDataExplorerStore } from '@/state/data-explorer.store';

// Types based on CONTRACT-001
interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  // Orderflow metrics
  delta: number;
  buy_volume: number;
  sell_volume: number;
  cumulative_delta: number;
  buy_trades: number;
  sell_trades: number;
  delta_percentage: number;
  max_delta: number;
  min_delta: number;
  delta_change: number;
  // Price levels & statistics
  vwap: number;
  typical_price: number;
  range: number;
  body_size: number;
  wick_upper: number;
  wick_lower: number;
  body_percentage: number;
  price_change: number;
  price_change_percentage: number;
  cumulative_volume: number;
  // Market microstructure
  tick_count: number;
  bid_volume: number;
  ask_volume: number;
  imbalance: number;
  spread_avg: number;
  trade_intensity: number;
  volume_rate: number;
  large_trade_count: number;
  large_trade_volume: number;
}

interface CandlesResponse {
  data: Candle[];
  total: number;
  has_more: boolean;
}

interface TimeframeCoverage {
  tf: string;
  count: number;
  start: string;
  end: string;
  last_updated: string;
}

interface CoverageResponse {
  timeframes: TimeframeCoverage[];
}

interface Contract {
  symbol: string;
  expiry: string;
  is_front_month: boolean;
}

interface ActiveContractsResponse {
  contracts: Contract[];
}

interface ExportJobStatus {
  status: 'queued' | 'processing' | 'complete' | 'failed';
  download_url?: string;
  size_mb?: number;
  error_message?: string;
  progress?: number;
}

const TIMEFRAMES = [
  { value: '1min', label: '1 Minute' },
  { value: '5min', label: '5 Minutes' },
  { value: '15min', label: '15 Minutes' },
  { value: '30min', label: '30 Minutes' },
  { value: '1hour', label: '1 Hour' },
  { value: '4hour', label: '4 Hour' },
  { value: '1day', label: '1 Day' },
];

const DataExplorer: React.FC = () => {
  const queryClient = useQueryClient();

  // Zustand store for state management
  const {
    selectedTimeframe,
    setSelectedTimeframe,
    dateRange,
    setDateRange,
    includeOflow,
    setIncludeOflow,
    selectedContract,
    setSelectedContract,
  } = useDataExplorerStore();

  const [exportJobId, setExportJobId] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  // Fetch candles data
  const { data: candlesData, isLoading: candlesLoading, error: candlesError, refetch: refetchCandles } = useQuery<CandlesResponse>({
    queryKey: ['candles', selectedTimeframe, selectedContract, dateRange, includeOflow],
    queryFn: async () => {
      const params = new URLSearchParams({
        tf: selectedTimeframe,
        symbol: selectedContract || 'NQH25',
        start: dateRange.start,
        end: dateRange.end,
        include_oflow: includeOflow.toString(),
        limit: '100',
      });

      const response = await fetch(`/api/v1/data/candles/${selectedTimeframe}?${params}`);
      if (!response.ok) throw new Error('Failed to fetch candles');
      return response.json();
    },
    enabled: !!selectedTimeframe && !!selectedContract,
  });

  // Fetch coverage data
  const { data: coverageData, isLoading: coverageLoading, refetch: refetchCoverage } = useQuery<CoverageResponse>({
    queryKey: ['coverage'],
    queryFn: async () => {
      const response = await fetch('/api/v1/data/coverage');
      if (!response.ok) throw new Error('Failed to fetch coverage');
      return response.json();
    },
  });

  // Fetch active contracts
  const { data: contractsData, isLoading: contractsLoading } = useQuery<ActiveContractsResponse>({
    queryKey: ['contracts'],
    queryFn: async () => {
      const response = await fetch('/api/v1/data/contracts/active');
      if (!response.ok) throw new Error('Failed to fetch contracts');
      return response.json();
    },
  });

  // Create export job mutation
  const createExportMutation = useMutation({
    mutationFn: async (params: { table: string; format: 'parquet' | 'csv' }) => {
      const response = await fetch('/api/v1/data/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table: params.table,
          start: dateRange.start,
          end: dateRange.end,
          include_oflow: includeOflow,
          format: params.format,
        }),
      });
      if (!response.ok) throw new Error('Failed to create export job');
      return response.json();
    },
    onSuccess: (data) => {
      setExportJobId(data.job_id);
      setIsExporting(true);
      toast({
        title: 'Export Started',
        description: `Export job ${data.job_id} has been queued.`,
      });
      pollExportStatus(data.job_id);
    },
    onError: (error) => {
      toast({
        title: 'Export Failed',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Poll export status
  const pollExportStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/data/export/${jobId}`);
        if (!response.ok) throw new Error('Failed to check export status');

        const status: ExportJobStatus = await response.json();

        if (status.status === 'complete') {
          clearInterval(interval);
          setIsExporting(false);
          toast({
            title: 'Export Complete',
            description: (
              <div className="flex flex-col gap-2">
                <span>Your export is ready for download ({status.size_mb?.toFixed(2)} MB)</span>
                {status.download_url && (
                  <a
                    href={status.download_url}
                    className="text-blue-500 hover:underline"
                    download
                  >
                    Click here to download
                  </a>
                )}
              </div>
            ),
          });
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setIsExporting(false);
          toast({
            title: 'Export Failed',
            description: status.error_message || 'Unknown error occurred',
            variant: 'destructive',
          });
        }
      } catch (error) {
        clearInterval(interval);
        setIsExporting(false);
        console.error('Error polling export status:', error);
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleExport = (format: 'parquet' | 'csv') => {
    const table = `candles_${selectedTimeframe}` as const;
    createExportMutation.mutate({ table, format });
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return num?.toFixed(decimals) || '0.00';
  };

  const formatVolume = (vol: number) => {
    if (vol >= 1000000) return `${(vol / 1000000).toFixed(1)}M`;
    if (vol >= 1000) return `${(vol / 1000).toFixed(1)}K`;
    return vol.toString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Explorer</h1>
          <p className="text-muted-foreground mt-1">
            Explore candles data, view coverage, and export datasets
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetchCandles();
              refetchCoverage();
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <Tabs defaultValue="candles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="candles">Candle Viewer</TabsTrigger>
          <TabsTrigger value="coverage">Coverage Dashboard</TabsTrigger>
        </TabsList>

        {/* Candle Viewer Tab */}
        <TabsContent value="candles" className="space-y-4">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">Candle Data Viewer</h2>
              <div className="flex items-center gap-4">
                {/* Contract Selector */}
                <Select value={selectedContract} onValueChange={setSelectedContract}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Select contract" />
                  </SelectTrigger>
                  <SelectContent>
                    {contractsData?.contracts.map((contract) => (
                      <SelectItem key={contract.symbol} value={contract.symbol}>
                        {contract.symbol}
                        {contract.is_front_month && (
                          <Badge variant="secondary" className="ml-2">Front</Badge>
                        )}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Timeframe Selector */}
                <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Timeframe" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEFRAMES.map((tf) => (
                      <SelectItem key={tf.value} value={tf.value}>
                        {tf.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Date Range Selector */}
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                    className="px-3 py-1 border rounded-md"
                  />
                  <span className="text-muted-foreground">to</span>
                  <input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                    className="px-3 py-1 border rounded-md"
                  />
                </div>

                {/* Oflow Toggle */}
                <div className="flex items-center gap-2">
                  <Switch
                    id="oflow-toggle"
                    checked={includeOflow}
                    onCheckedChange={setIncludeOflow}
                  />
                  <Label htmlFor="oflow-toggle" className="cursor-pointer">
                    {includeOflow ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    <span className="ml-2">Order Flow</span>
                  </Label>
                </div>
              </div>
            </div>

            {/* Candles Table */}
            {candlesLoading ? (
              <div className="flex items-center justify-center h-64">
                <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : candlesError ? (
              <Alert variant="destructive">
                <AlertDescription>
                  Error loading candles: {(candlesError as Error).message}
                </AlertDescription>
              </Alert>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Open</TableHead>
                      <TableHead>High</TableHead>
                      <TableHead>Low</TableHead>
                      <TableHead>Close</TableHead>
                      <TableHead>Volume</TableHead>
                      {includeOflow && (
                        <>
                          <TableHead>Delta</TableHead>
                          <TableHead>Buy Vol</TableHead>
                          <TableHead>Sell Vol</TableHead>
                          <TableHead>VWAP</TableHead>
                          <TableHead>Imbalance</TableHead>
                        </>
                      )}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {candlesData?.data.map((candle) => (
                      <TableRow key={candle.timestamp}>
                        <TableCell className="font-mono text-xs">
                          {format(new Date(candle.timestamp), 'MM/dd HH:mm')}
                        </TableCell>
                        <TableCell>{formatNumber(candle.open)}</TableCell>
                        <TableCell>{formatNumber(candle.high)}</TableCell>
                        <TableCell>{formatNumber(candle.low)}</TableCell>
                        <TableCell>{formatNumber(candle.close)}</TableCell>
                        <TableCell>{formatVolume(candle.volume)}</TableCell>
                        {includeOflow && (
                          <>
                            <TableCell className={cn(
                              candle.delta > 0 ? 'text-green-600' : 'text-red-600'
                            )}>
                              {candle.delta}
                            </TableCell>
                            <TableCell className="text-green-600">
                              {formatVolume(candle.buy_volume)}
                            </TableCell>
                            <TableCell className="text-red-600">
                              {formatVolume(candle.sell_volume)}
                            </TableCell>
                            <TableCell>{formatNumber(candle.vwap)}</TableCell>
                            <TableCell className={cn(
                              candle.imbalance > 0 ? 'text-green-600' : 'text-red-600'
                            )}>
                              {formatNumber(candle.imbalance * 100)}%
                            </TableCell>
                          </>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {candlesData?.has_more && (
                  <div className="text-center mt-4 text-sm text-muted-foreground">
                    Showing first 100 candles. Total: {candlesData.total}
                  </div>
                )}
              </div>
            )}

            {/* Export Controls */}
            <div className="mt-6 flex items-center justify-between border-t pt-6">
              <div className="text-sm text-muted-foreground">
                {candlesData && (
                  <span>
                    {candlesData.total} candles available for export
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleExport('csv')}
                  disabled={isExporting || !candlesData?.data.length}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
                <Button
                  onClick={() => handleExport('parquet')}
                  disabled={isExporting || !candlesData?.data.length}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Parquet
                </Button>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* Coverage Dashboard Tab */}
        <TabsContent value="coverage" className="space-y-4">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">Data Coverage Dashboard</h2>
              <Badge variant="outline">
                <Database className="h-3 w-3 mr-1" />
                Last Updated: {coverageData?.timeframes[0]?.last_updated
                  ? format(new Date(coverageData.timeframes[0].last_updated), 'MMM dd, yyyy HH:mm')
                  : 'N/A'
                }
              </Badge>
            </div>

            {coverageLoading ? (
              <div className="flex items-center justify-center h-64">
                <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timeframe</TableHead>
                      <TableHead className="text-right">Candle Count</TableHead>
                      <TableHead>Start Date</TableHead>
                      <TableHead>End Date</TableHead>
                      <TableHead>Coverage</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {coverageData?.timeframes.map((tf) => {
                      const startDate = new Date(tf.start);
                      const endDate = new Date(tf.end);
                      const daysCovered = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

                      return (
                        <TableRow key={tf.tf}>
                          <TableCell className="font-medium">
                            {TIMEFRAMES.find(t => t.value === tf.tf)?.label || tf.tf}
                          </TableCell>
                          <TableCell className="text-right font-mono">
                            {tf.count.toLocaleString()}
                          </TableCell>
                          <TableCell>
                            {format(startDate, 'MMM dd, yyyy')}
                          </TableCell>
                          <TableCell>
                            {format(endDate, 'MMM dd, yyyy')}
                          </TableCell>
                          <TableCell>
                            {daysCovered} days
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={tf.count > 10000 ? 'default' : tf.count > 1000 ? 'secondary' : 'outline'}
                            >
                              {tf.count > 10000 ? 'Complete' : tf.count > 1000 ? 'Partial' : 'Limited'}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Active Contracts Section */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-4">Active Contracts</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {contractsData?.contracts.map((contract) => (
                  <Card key={contract.symbol} className={cn(
                    "p-4 cursor-pointer hover:shadow-md transition-shadow",
                    contract.is_front_month && "border-primary"
                  )}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{contract.symbol}</p>
                        <p className="text-sm text-muted-foreground">
                          Expires: {format(new Date(contract.expiry), 'MMM dd, yyyy')}
                        </p>
                      </div>
                      {contract.is_front_month && (
                        <Badge>Front Month</Badge>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DataExplorer;