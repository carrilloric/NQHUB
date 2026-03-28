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
  Droplets,
  BarChart3,
  Target,
  Shield,
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
  LiquidityPoolPattern,
  LiquidityPoolFilters,
  LiquidityPoolStatus,
  LiquidityPoolStrength,
  LiquidityPoolType,
  PaginatedResponse,
} from '@shared/types/patterns.types';

interface LiquidityPoolViewerProps {
  filters: LiquidityPoolFilters;
  onFiltersChange: (filters: LiquidityPoolFilters) => void;
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

export function LiquidityPoolViewer({
  filters,
  onFiltersChange,
  isLoading,
  onLoadingChange,
}: LiquidityPoolViewerProps) {
  const [patterns, setPatterns] = useState<LiquidityPoolPattern[]>([]);
  const [totalPatterns, setTotalPatterns] = useState(0);
  const [selectedPattern, setSelectedPattern] = useState<LiquidityPoolPattern | null>(null);
  const [error, setError] = useState<string | null>(null);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  // Fetch Liquidity Pool patterns
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

        const response = await fetch(`/api/v1/patterns/liquidity-pools?${params}`);
        if (!response.ok) {
          throw new Error('Failed to fetch Liquidity Pool patterns');
        }

        const data: PaginatedResponse<LiquidityPoolPattern> = await response.json();
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

  // Draw Liquidity Pool zones on chart
  useEffect(() => {
    if (!candleSeriesRef.current || !patterns.length) return;

    // Clear existing markers
    (candleSeriesRef.current as any)?.setMarkers([]);

    // Add Liquidity Pool zones as horizontal zones (simplified visualization)
    patterns.slice(0, 10).forEach((pattern) => {
      const color = getPoolTypeColor(pattern.pool_type);

      // Add zone high line
      candleSeriesRef.current?.createPriceLine({
        price: pattern.zone_high,
        color: color,
        lineWidth: 2,
        lineStyle: 3, // Dotted
        title: `LP ${pattern.pool_type}`,
      });

      // Add zone low line
      candleSeriesRef.current?.createPriceLine({
        price: pattern.zone_low,
        color: color,
        lineWidth: 2,
        lineStyle: 3, // Dotted
        title: '',
      });

      // Add modal level
      if (pattern.modal_level) {
        candleSeriesRef.current?.createPriceLine({
          price: pattern.modal_level,
          color: '#F59E0B',
          lineWidth: 1,
          lineStyle: 0, // Solid
          title: 'Modal',
        });
      }
    });
  }, [patterns]);

  // Get pool type color
  const getPoolTypeColor = (type: LiquidityPoolType) => {
    if (type === 'EQH' || type === 'SWING_HIGH') return '#10B981'; // Green for highs
    if (type === 'EQL' || type === 'SWING_LOW') return '#EF4444'; // Red for lows
    if (type.includes('NY')) return '#8B5CF6'; // Purple for New York session
    if (type.includes('AS')) return '#3B82F6'; // Blue for Asian session
    if (type.includes('LS')) return '#F59E0B'; // Amber for London session
    return '#6B7280'; // Gray default
  };

  // Handle status filter change
  const handleStatusChange = (status: string) => {
    onFiltersChange({
      ...filters,
      status: status === 'all' ? undefined : (status as LiquidityPoolStatus),
    });
  };

  // Handle type filter change
  const handleTypeChange = (poolType: string) => {
    onFiltersChange({
      ...filters,
      pool_type: poolType === 'all' ? undefined : (poolType as LiquidityPoolType),
    });
  };

  // Handle strength filter change
  const handleStrengthChange = (strength: string) => {
    onFiltersChange({
      ...filters,
      strength: strength === 'all' ? undefined : (strength as LiquidityPoolStrength),
    });
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    onFiltersChange({ ...filters, page: newPage });
  };

  // Get status badge color
  const getStatusColor = (status: LiquidityPoolStatus) => {
    switch (status) {
      case 'UNMITIGATED':
        return 'bg-blue-500';
      case 'RESPECTED':
        return 'bg-green-500';
      case 'SWEPT':
        return 'bg-yellow-500';
      case 'MITIGATED':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get strength badge color
  const getStrengthColor = (strength: LiquidityPoolStrength) => {
    switch (strength) {
      case 'STRONG':
        return 'bg-green-500';
      case 'NORMAL':
        return 'bg-yellow-500';
      case 'WEAK':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Get pool type badge
  const getPoolTypeBadge = (type: LiquidityPoolType) => {
    let color = 'bg-gray-500';
    let icon = null;

    if (type === 'EQH' || type === 'EQL') {
      color = 'bg-blue-500';
      icon = '=';
    } else if (type.includes('NY')) {
      color = 'bg-purple-500';
      icon = 'NY';
    } else if (type.includes('AS')) {
      color = 'bg-indigo-500';
      icon = 'AS';
    } else if (type.includes('LS')) {
      color = 'bg-amber-500';
      icon = 'LS';
    } else if (type.includes('SWING')) {
      color = 'bg-teal-500';
      icon = '↕';
    }

    return { color, icon };
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
              Candlestick Chart with Liquidity Pool Overlay
            </CardTitle>
            <div className="flex items-center gap-2">
              {selectedPattern && (
                <Badge variant="outline">
                  Selected: LP #{selectedPattern.id}
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
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="UNMITIGATED">Unmitigated</SelectItem>
            <SelectItem value="RESPECTED">Respected</SelectItem>
            <SelectItem value="SWEPT">Swept</SelectItem>
            <SelectItem value="MITIGATED">Mitigated</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.pool_type || 'all'} onValueChange={handleTypeChange}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="EQH">Equal Highs</SelectItem>
            <SelectItem value="EQL">Equal Lows</SelectItem>
            <SelectItem value="NYH">NY High</SelectItem>
            <SelectItem value="NYL">NY Low</SelectItem>
            <SelectItem value="ASH">Asian High</SelectItem>
            <SelectItem value="ASL">Asian Low</SelectItem>
            <SelectItem value="LSH">London High</SelectItem>
            <SelectItem value="LSL">London Low</SelectItem>
            <SelectItem value="SWING_HIGH">Swing High</SelectItem>
            <SelectItem value="SWING_LOW">Swing Low</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.strength || 'all'} onValueChange={handleStrengthChange}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Filter by strength" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Strengths</SelectItem>
            <SelectItem value="STRONG">Strong</SelectItem>
            <SelectItem value="NORMAL">Normal</SelectItem>
            <SelectItem value="WEAK">Weak</SelectItem>
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
          <CardTitle className="text-lg">Detected Liquidity Pools</CardTitle>
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
              No Liquidity Pool patterns found for the selected filters
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Formation Time</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Zone Range</TableHead>
                    <TableHead>Modal Level</TableHead>
                    <TableHead>Touches</TableHead>
                    <TableHead>Strength</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {patterns.map((pattern) => {
                    const typeInfo = getPoolTypeBadge(pattern.pool_type);
                    return (
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
                            className={cn("text-xs", typeInfo.color)}
                          >
                            {pattern.pool_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {pattern.zone_low.toFixed(2)} - {pattern.zone_high.toFixed(2)}
                        </TableCell>
                        <TableCell className="font-mono">
                          {pattern.modal_level?.toFixed(2) || '-'}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {pattern.touches || 0}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={cn("text-xs", getStrengthColor(pattern.strength))}
                          >
                            {pattern.strength}
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
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedPattern(pattern);
                              // Scroll chart to pattern time
                            }}
                          >
                            <Droplets className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
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
            <CardTitle className="text-lg">Liquidity Pool #{selectedPattern.id} Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Zone Height</p>
                <p className="font-mono font-medium">
                  {(selectedPattern.zone_high - selectedPattern.zone_low).toFixed(2)} pts
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Modal Level</p>
                <p className="font-mono font-medium">
                  {selectedPattern.modal_level?.toFixed(2) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Touches Count</p>
                <p className="font-medium flex items-center gap-2">
                  <Target className="h-4 w-4 text-blue-500" />
                  {selectedPattern.touches || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Sweep Time</p>
                <p className="font-medium">
                  {selectedPattern.sweep_time
                    ? format(new Date(selectedPattern.sweep_time), 'MMM dd, HH:mm:ss')
                    : 'Not swept'}
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
                <p className="text-sm text-muted-foreground">Protection</p>
                <p className="font-medium flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-500" />
                  {selectedPattern.status === 'RESPECTED' ? 'Active' : 'Inactive'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}