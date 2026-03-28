import React, { useState, useEffect } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { AssistantPanelSidebar } from '@/assistant';
import { useI18n } from '@/state/app';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { CalendarIcon, RefreshCcw, Filter, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

// Import pattern components
import { FVGViewer } from '@/components/patterns/FVGViewer';
import { OrderBlockViewer } from '@/components/patterns/OrderBlockViewer';
import { LiquidityPoolViewer } from '@/components/patterns/LiquidityPoolViewer';

// Import types
import type {
  Timeframe,
  FVGFilters,
  OrderBlockFilters,
  LiquidityPoolFilters,
} from '@shared/types/patterns.types';

type PatternTab = 'fvg' | 'orderblocks' | 'liquiditypools';

// Available timeframes
const TIMEFRAMES: Timeframe[] = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day'];

// Default filters
const DEFAULT_FVG_FILTERS: FVGFilters = {
  symbol: 'NQH25',
  timeframe: '5min',
  page: 1,
  page_size: 50,
};

const DEFAULT_OB_FILTERS: OrderBlockFilters = {
  symbol: 'NQH25',
  timeframe: '5min',
  page: 1,
  page_size: 50,
};

const DEFAULT_LP_FILTERS: LiquidityPoolFilters = {
  symbol: 'NQH25',
  timeframe: '5min',
  page: 1,
  page_size: 50,
};

export function PatternDetection() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<PatternTab>('fvg');

  // Filter states for each pattern type
  const [fvgFilters, setFvgFilters] = useState<FVGFilters>(DEFAULT_FVG_FILTERS);
  const [obFilters, setObFilters] = useState<OrderBlockFilters>(DEFAULT_OB_FILTERS);
  const [lpFilters, setLpFilters] = useState<LiquidityPoolFilters>(DEFAULT_LP_FILTERS);

  // Date range states
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);

  // Loading states
  const [isLoadingFVG, setIsLoadingFVG] = useState(false);
  const [isLoadingOB, setIsLoadingOB] = useState(false);
  const [isLoadingLP, setIsLoadingLP] = useState(false);

  // Handle timeframe change
  const handleTimeframeChange = (timeframe: Timeframe) => {
    switch (activeTab) {
      case 'fvg':
        setFvgFilters(prev => ({ ...prev, timeframe }));
        break;
      case 'orderblocks':
        setObFilters(prev => ({ ...prev, timeframe }));
        break;
      case 'liquiditypools':
        setLpFilters(prev => ({ ...prev, timeframe }));
        break;
    }
  };

  // Handle date range change
  const handleDateRangeChange = () => {
    const dateFilters = {
      start_date: startDate ? format(startDate, 'yyyy-MM-dd') : undefined,
      end_date: endDate ? format(endDate, 'yyyy-MM-dd') : undefined,
    };

    switch (activeTab) {
      case 'fvg':
        setFvgFilters(prev => ({ ...prev, ...dateFilters }));
        break;
      case 'orderblocks':
        setObFilters(prev => ({ ...prev, ...dateFilters }));
        break;
      case 'liquiditypools':
        setLpFilters(prev => ({ ...prev, ...dateFilters }));
        break;
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    switch (activeTab) {
      case 'fvg':
        setIsLoadingFVG(true);
        // Trigger FVG data refresh
        setTimeout(() => setIsLoadingFVG(false), 1000);
        break;
      case 'orderblocks':
        setIsLoadingOB(true);
        // Trigger OB data refresh
        setTimeout(() => setIsLoadingOB(false), 1000);
        break;
      case 'liquiditypools':
        setIsLoadingLP(true);
        // Trigger LP data refresh
        setTimeout(() => setIsLoadingLP(false), 1000);
        break;
    }
  };

  // Get current timeframe based on active tab
  const getCurrentTimeframe = () => {
    switch (activeTab) {
      case 'fvg':
        return fvgFilters.timeframe;
      case 'orderblocks':
        return obFilters.timeframe;
      case 'liquiditypools':
        return lpFilters.timeframe;
      default:
        return '5min';
    }
  };

  // Get loading state
  const isLoading = () => {
    switch (activeTab) {
      case 'fvg':
        return isLoadingFVG;
      case 'orderblocks':
        return isLoadingOB;
      case 'liquiditypools':
        return isLoadingLP;
      default:
        return false;
    }
  };

  return (
    <>
      <Sidebar />
      <AssistantPanelSidebar />
      <main className="flex-1 overflow-y-auto">
        {/* Page header */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold">Pattern Detection</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                ICT pattern analysis with candlestick chart overlays
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading()}
              >
                <RefreshCcw className={cn("h-4 w-4 mr-2", isLoading() && "animate-spin")} />
                Refresh
              </Button>
            </div>
          </div>

          {/* Filters section */}
          <Card className="mb-6">
            <CardHeader className="py-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Filter className="h-4 w-4" />
                  Filters
                </CardTitle>
                <div className="flex items-center gap-4">
                  {/* Timeframe selector */}
                  <div className="flex items-center gap-2">
                    <Label htmlFor="timeframe">Timeframe:</Label>
                    <Select
                      value={getCurrentTimeframe()}
                      onValueChange={(value) => handleTimeframeChange(value as Timeframe)}
                    >
                      <SelectTrigger id="timeframe" className="w-[120px]">
                        <SelectValue placeholder="Select timeframe" />
                      </SelectTrigger>
                      <SelectContent>
                        {TIMEFRAMES.map((tf) => (
                          <SelectItem key={tf} value={tf}>
                            {tf}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Date range selector */}
                  <div className="flex items-center gap-2">
                    <Label>Date Range:</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className={cn(
                            "w-[200px] justify-start text-left font-normal",
                            !startDate && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {startDate ? format(startDate, 'PPP') : 'Start date'}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={startDate}
                          onSelect={setStartDate}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>

                    <span className="text-sm text-gray-500">to</span>

                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className={cn(
                            "w-[200px] justify-start text-left font-normal",
                            !endDate && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {endDate ? format(endDate, 'PPP') : 'End date'}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={endDate}
                          onSelect={setEndDate}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>

                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleDateRangeChange}
                      disabled={!startDate && !endDate}
                    >
                      Apply
                    </Button>
                  </div>

                  {/* Symbol input */}
                  <div className="flex items-center gap-2">
                    <Label htmlFor="symbol">Symbol:</Label>
                    <Input
                      id="symbol"
                      type="text"
                      value={fvgFilters.symbol}
                      onChange={(e) => {
                        const symbol = e.target.value.toUpperCase();
                        setFvgFilters(prev => ({ ...prev, symbol }));
                        setObFilters(prev => ({ ...prev, symbol }));
                        setLpFilters(prev => ({ ...prev, symbol }));
                      }}
                      className="w-[100px]"
                      placeholder="NQH25"
                    />
                  </div>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Pattern tabs */}
          <Tabs
            value={activeTab}
            onValueChange={(value) => setActiveTab(value as PatternTab)}
            className="space-y-4"
          >
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="fvg" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Fair Value Gaps
              </TabsTrigger>
              <TabsTrigger value="orderblocks" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Order Blocks
              </TabsTrigger>
              <TabsTrigger value="liquiditypools" className="flex items-center gap-2">
                <TrendingDown className="h-4 w-4" />
                Liquidity Pools
              </TabsTrigger>
            </TabsList>

            {/* FVG Tab */}
            <TabsContent value="fvg" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Fair Value Gaps (FVG)</CardTitle>
                  <CardDescription>
                    Price gaps created by imbalance between buyers and sellers
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <FVGViewer
                    filters={fvgFilters}
                    onFiltersChange={setFvgFilters}
                    isLoading={isLoadingFVG}
                    onLoadingChange={setIsLoadingFVG}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Order Blocks Tab */}
            <TabsContent value="orderblocks" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Order Blocks</CardTitle>
                  <CardDescription>
                    Last candle before significant impulse move, represents institutional order placement
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <OrderBlockViewer
                    filters={obFilters}
                    onFiltersChange={setObFilters}
                    isLoading={isLoadingOB}
                    onLoadingChange={setIsLoadingOB}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Liquidity Pools Tab */}
            <TabsContent value="liquiditypools" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Liquidity Pools</CardTitle>
                  <CardDescription>
                    Areas where stop-loss orders accumulate, creating liquidity
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <LiquidityPoolViewer
                    filters={lpFilters}
                    onFiltersChange={setLpFilters}
                    isLoading={isLoadingLP}
                    onLoadingChange={setIsLoadingLP}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </>
  );
}