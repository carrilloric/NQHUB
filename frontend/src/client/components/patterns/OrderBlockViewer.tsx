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
  BarChart3,
  Zap,
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
  OrderBlockPattern,
  OrderBlockFilters,
  OrderBlockStatus,
  OrderBlockQuality,
  OrderBlockType,
  PaginatedResponse,
} from '@shared/types/patterns.types';

interface OrderBlockViewerProps {
  filters: OrderBlockFilters;
  onFiltersChange: (filters: OrderBlockFilters) => void;
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

export function OrderBlockViewer({
  filters,
  onFiltersChange,
  isLoading,
  onLoadingChange,
}: OrderBlockViewerProps) {
  const [patterns, setPatterns] = useState<OrderBlockPattern[]>([]);
  const [totalPatterns, setTotalPatterns] = useState(0);
  const [selectedPattern, setSelectedPattern] = useState<OrderBlockPattern | null>(null);
  const [error, setError] = useState<string | null>(null);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  // Fetch Order Block patterns
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

        const response = await fetch(`/api/v1/patterns/order-blocks?${params}`);
        if (!response.ok) {
          throw new Error('Failed to fetch Order Block patterns');
        }

        const data: PaginatedResponse<OrderBlockPattern> = await response.json();
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

  // Draw Order Block zones on chart
  useEffect(() => {
    if (!candleSeriesRef.current || !patterns.length) return;

    // Clear existing markers
    (candleSeriesRef.current as any)?.setMarkers([]);

    // Add Order Block zones as rectangles (simplified visualization)
    patterns.slice(0, 10).forEach((pattern) => {
      const isBullish = pattern.ob_type.includes('BULLISH');
      const color = isBullish ? '#10B981' : '#EF4444';

      // Add OB high line
      candleSeriesRef.current?.createPriceLine({
        price: pattern.ob_high,
        color: color,
        lineWidth: 2,
        lineStyle: 0, // Solid
        title: `OB ${pattern.id}`,
      });

      // Add OB low line
      candleSeriesRef.current?.createPriceLine({
        price: pattern.ob_low,
        color: color,
        lineWidth: 2,
        lineStyle: 0, // Solid
        title: '',
      });

      // Add body midpoint
      if (pattern.ob_body_midpoint) {
        candleSeriesRef.current?.createPriceLine({
          price: pattern.ob_body_midpoint,
          color: '#F59E0B',
          lineWidth: 1,
          lineStyle: 2, // Dashed
          title: 'Mid',
        });
      }
    });
  }, [patterns]);

  // Handle status filter change
  const handleStatusChange = (status: string) => {
    onFiltersChange({
      ...filters,
      status: status === 'all' ? undefined : (status as OrderBlockStatus),
    });
  };

  // Handle type filter change
  const handleTypeChange = (obType: string) => {
    onFiltersChange({
      ...filters,
      ob_type: obType === 'all' ? undefined : (obType as OrderBlockType),
    });
  };

  // Handle quality filter change
  const handleQualityChange = (quality: string) => {
    onFiltersChange({
      ...filters,
      quality: quality === 'all' ? undefined : (quality as OrderBlockQuality),
    });
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    onFiltersChange({ ...filters, page: newPage });
  };

  // Get status badge color
  const getStatusColor = (status: OrderBlockStatus) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-500';
      case 'TESTED':
        return 'bg-yellow-500';
      case 'BROKEN':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get quality badge color
  const getQualityColor = (quality: OrderBlockQuality) => {
    switch (quality) {
      case 'HIGH':
        return 'bg-green-500';
      case 'MEDIUM':
        return 'bg-yellow-500';
      case 'LOW':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get type badge color
  const getTypeColor = (type: OrderBlockType) => {
    if (type.includes('STRONG')) {
      return type.includes('BULLISH') ? 'bg-green-600' : 'bg-red-600';
    }
    return type.includes('BULLISH') ? 'bg-green-500' : 'bg-red-500';
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
              Candlestick Chart with Order Block Overlay
            </CardTitle>
            <div className="flex items-center gap-2">
              {selectedPattern && (
                <Badge variant="outline">
                  Selected: OB #{selectedPattern.id}
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
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="ACTIVE">Active</SelectItem>
            <SelectItem value="TESTED">Tested</SelectItem>
            <SelectItem value="BROKEN">Broken</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.ob_type || 'all'} onValueChange={handleTypeChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="BULLISH OB">Bullish OB</SelectItem>
            <SelectItem value="BEARISH OB">Bearish OB</SelectItem>
            <SelectItem value="STRONG BULLISH OB">Strong Bullish</SelectItem>
            <SelectItem value="STRONG BEARISH OB">Strong Bearish</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.quality || 'all'} onValueChange={handleQualityChange}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Filter by quality" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Qualities</SelectItem>
            <SelectItem value="HIGH">High</SelectItem>
            <SelectItem value="MEDIUM">Medium</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
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
          <CardTitle className="text-lg">Detected Order Blocks</CardTitle>
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
              No Order Block patterns found for the selected filters
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Formation Time</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>OB Range</TableHead>
                    <TableHead>Impulse</TableHead>
                    <TableHead>Quality</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Volume</TableHead>
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
                        <Badge
                          variant="secondary"
                          className={cn("text-xs", getTypeColor(pattern.ob_type))}
                        >
                          {pattern.ob_type.replace(' OB', '')}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {pattern.ob_low.toFixed(2)} - {pattern.ob_high.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {pattern.impulse_direction === 'UP' ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                          <span className="font-mono">{pattern.impulse_move?.toFixed(1)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn("text-xs", getQualityColor(pattern.quality))}
                        >
                          {pattern.quality}
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
                      <TableCell className="font-mono">
                        {pattern.volume?.toLocaleString() || '-'}
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
                          <Zap className="h-4 w-4" />
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
            <CardTitle className="text-lg">Order Block #{selectedPattern.id} Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Body Midpoint</p>
                <p className="font-mono font-medium">
                  {selectedPattern.ob_body_midpoint?.toFixed(2) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Range Midpoint</p>
                <p className="font-mono font-medium">
                  {selectedPattern.ob_range_midpoint?.toFixed(2) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Impulse Move</p>
                <p className="font-mono font-medium">
                  {selectedPattern.impulse_move?.toFixed(2) || '-'} pts
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Impulse Direction</p>
                <p className="font-medium flex items-center gap-1">
                  {selectedPattern.impulse_direction === 'UP' ? (
                    <>
                      <TrendingUp className="h-4 w-4 text-green-500" />
                      UP
                    </>
                  ) : (
                    <>
                      <TrendingDown className="h-4 w-4 text-red-500" />
                      DOWN
                    </>
                  )}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Test Time</p>
                <p className="font-medium">
                  {selectedPattern.test_time
                    ? format(new Date(selectedPattern.test_time), 'MMM dd, HH:mm:ss')
                    : 'Not tested'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Break Time</p>
                <p className="font-medium">
                  {selectedPattern.break_time
                    ? format(new Date(selectedPattern.break_time), 'MMM dd, HH:mm:ss')
                    : 'Not broken'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}