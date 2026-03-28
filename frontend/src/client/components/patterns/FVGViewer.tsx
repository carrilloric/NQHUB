import React, { useEffect, useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

// Import lightweight-charts
import {
  createChart,
  ColorType,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  Time,
} from 'lightweight-charts';

import type {
  FVGPattern,
  FVGFilters,
  FVGStatus,
  FVGSignificance,
  PaginatedResponse,
} from '@shared/types/patterns.types';

interface FVGViewerProps {
  filters: FVGFilters;
  onFiltersChange: (filters: FVGFilters) => void;
  isLoading: boolean;
  onLoadingChange: (loading: boolean) => void;
}

// Mock candlestick data generator
function generateCandlestickData(startTime: Date, count: number = 100): CandlestickData[] {
  const data: CandlestickData[] = [];
  let basePrice = 20000;

  for (let i = 0; i < count; i++) {
    const time = new Date(startTime.getTime() + i * 5 * 60 * 1000); // 5-minute intervals
    const open = basePrice + (Math.random() - 0.5) * 50;
    const close = open + (Math.random() - 0.5) * 50;
    const high = Math.max(open, close) + Math.random() * 20;
    const low = Math.min(open, close) - Math.random() * 20;

    data.push({
      time: (time.getTime() / 1000) as Time,
      open,
      high,
      low,
      close,
    });

    basePrice = close;
  }

  return data;
}

export function FVGViewer({
  filters,
  onFiltersChange,
  isLoading,
  onLoadingChange,
}: FVGViewerProps) {
  const [patterns, setPatterns] = useState<FVGPattern[]>([]);
  const [totalPatterns, setTotalPatterns] = useState(0);
  const [selectedPattern, setSelectedPattern] = useState<FVGPattern | null>(null);
  const [error, setError] = useState<string | null>(null);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  // Fetch FVG patterns
  useEffect(() => {
    const fetchPatterns = async () => {
      onLoadingChange(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, String(value));
          }
        });

        const response = await fetch(`/api/v1/patterns/fvgs?${params}`);
        if (!response.ok) {
          throw new Error('Failed to fetch FVG patterns');
        }

        const data: PaginatedResponse<FVGPattern> = await response.json();
        setPatterns(data.data);
        setTotalPatterns(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        onLoadingChange(false);
      }
    };

    fetchPatterns();
  }, [filters, onLoadingChange]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9CA3AF',
      },
      grid: {
        vertLines: { color: 'rgba(156, 163, 175, 0.1)' },
        horzLines: { color: 'rgba(156, 163, 175, 0.1)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(156, 163, 175, 0.3)',
      },
      timeScale: {
        borderColor: 'rgba(156, 163, 175, 0.3)',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = (chart as any).addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#EF4444',
      borderUpColor: '#10B981',
      borderDownColor: '#EF4444',
      wickUpColor: '#10B981',
      wickDownColor: '#EF4444',
    });

    // Load sample candlestick data
    const candleData = generateCandlestickData(new Date(Date.now() - 24 * 60 * 60 * 1000), 100);
    candleSeries.setData(candleData);

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Draw FVG zones on chart
  useEffect(() => {
    if (!candleSeriesRef.current || !patterns.length) return;

    // Clear existing markers
    (candleSeriesRef.current as any)?.setMarkers([]);

    // Add FVG zones as price lines (simplified visualization)
    patterns.slice(0, 10).forEach((pattern) => {
      // Add premium level line
      candleSeriesRef.current?.createPriceLine({
        price: pattern.gap_high,
        color: pattern.direction === 'BULLISH' ? '#10B981' : '#EF4444',
        lineWidth: 1,
        lineStyle: 2, // Dashed
        title: `FVG ${pattern.id}`,
      });

      // Add discount level line
      candleSeriesRef.current?.createPriceLine({
        price: pattern.gap_low,
        color: pattern.direction === 'BULLISH' ? '#10B981' : '#EF4444',
        lineWidth: 1,
        lineStyle: 2, // Dashed
        title: '',
      });

      // Add consequent encroachment (50% level)
      if (pattern.consequent_encroachment) {
        candleSeriesRef.current?.createPriceLine({
          price: pattern.consequent_encroachment,
          color: '#F59E0B',
          lineWidth: 1,
          lineStyle: 1, // Solid
          title: 'CE',
        });
      }
    });
  }, [patterns]);

  // Handle status filter change
  const handleStatusChange = (status: string) => {
    onFiltersChange({
      ...filters,
      status: status === 'all' ? undefined : (status as FVGStatus),
    });
  };

  // Handle significance filter change
  const handleSignificanceChange = (significance: string) => {
    onFiltersChange({
      ...filters,
      significance: significance === 'all' ? undefined : (significance as FVGSignificance),
    });
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    onFiltersChange({ ...filters, page: newPage });
  };

  // Get status badge color
  const getStatusColor = (status: FVGStatus) => {
    switch (status) {
      case 'UNMITIGATED':
        return 'bg-blue-500';
      case 'REDELIVERED':
        return 'bg-yellow-500';
      case 'REBALANCED':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get significance badge color
  const getSignificanceColor = (significance: FVGSignificance) => {
    switch (significance) {
      case 'EXTREME':
        return 'bg-red-500';
      case 'LARGE':
        return 'bg-orange-500';
      case 'MEDIUM':
        return 'bg-yellow-500';
      case 'SMALL':
        return 'bg-blue-500';
      case 'MICRO':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Calculate total pages
  const totalPages = Math.ceil(totalPatterns / (filters.page_size || 50));
  const currentPage = filters.page || 1;

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {/* Chart Section */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Candlestick Chart with FVG Overlay
            </CardTitle>
            <div className="flex items-center gap-2">
              {selectedPattern && (
                <Badge variant="outline">
                  Selected: FVG #{selectedPattern.id}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div ref={chartContainerRef} className="w-full h-[400px]" />
        </CardContent>
      </Card>

      {/* Filter Controls */}
      <div className="flex items-center gap-4">
        <Select value={filters.status || 'all'} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="UNMITIGATED">Unmitigated</SelectItem>
            <SelectItem value="REDELIVERED">Redelivered</SelectItem>
            <SelectItem value="REBALANCED">Rebalanced</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.significance || 'all'} onValueChange={handleSignificanceChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by significance" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Significances</SelectItem>
            <SelectItem value="EXTREME">Extreme</SelectItem>
            <SelectItem value="LARGE">Large</SelectItem>
            <SelectItem value="MEDIUM">Medium</SelectItem>
            <SelectItem value="SMALL">Small</SelectItem>
            <SelectItem value="MICRO">Micro</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex-1" />

        <div className="text-sm text-muted-foreground">
          Showing {patterns.length} of {totalPatterns} patterns
        </div>
      </div>

      {/* Patterns Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Detected FVG Patterns</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : patterns.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No FVG patterns found for the selected filters
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Formation Time</TableHead>
                    <TableHead>Direction</TableHead>
                    <TableHead>Gap Range</TableHead>
                    <TableHead>Size (pts)</TableHead>
                    <TableHead>Size (%)</TableHead>
                    <TableHead>Significance</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>BOS</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {patterns.map((pattern) => (
                    <TableRow
                      key={pattern.id}
                      className={cn(
                        "cursor-pointer hover:bg-muted/50",
                        selectedPattern?.id === pattern.id && "bg-muted"
                      )}
                      onClick={() => setSelectedPattern(pattern)}
                    >
                      <TableCell className="font-mono">#{pattern.id}</TableCell>
                      <TableCell>
                        {format(new Date(pattern.formation_time), 'MMM dd, HH:mm')}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {pattern.direction === 'BULLISH' ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                          <span>{pattern.direction}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {pattern.gap_low.toFixed(2)} - {pattern.gap_high.toFixed(2)}
                      </TableCell>
                      <TableCell className="font-mono">
                        {pattern.gap_size_pts.toFixed(2)}
                      </TableCell>
                      <TableCell className="font-mono">
                        {pattern.gap_size_pct.toFixed(3)}%
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn(
                            "text-xs",
                            getSignificanceColor(pattern.significance)
                          )}
                        >
                          {pattern.significance}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn("text-xs", getStatusColor(pattern.status))}
                        >
                          {pattern.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {pattern.has_break_of_structure ? (
                          <Badge variant="outline" className="text-xs">
                            Yes
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedPattern(pattern);
                            // Scroll chart to pattern time
                          }}
                        >
                          <Activity className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <div className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Selected Pattern Details */}
      {selectedPattern && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">FVG #{selectedPattern.id} Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Premium Level</p>
                <p className="font-mono font-medium">
                  {selectedPattern.premium_level?.toFixed(2) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Discount Level</p>
                <p className="font-mono font-medium">
                  {selectedPattern.discount_level?.toFixed(2) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Consequent Encroachment</p>
                <p className="font-mono font-medium">
                  {selectedPattern.consequent_encroachment?.toFixed(2) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Displacement Score</p>
                <p className="font-mono font-medium">
                  {selectedPattern.displacement_score?.toFixed(3) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Mitigation Time</p>
                <p className="font-medium">
                  {selectedPattern.mitigation_time
                    ? format(new Date(selectedPattern.mitigation_time), 'MMM dd, HH:mm:ss')
                    : 'Not mitigated'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Mitigation Candle</p>
                <p className="font-mono font-medium">
                  {selectedPattern.mitigation_candle_id || '-'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}