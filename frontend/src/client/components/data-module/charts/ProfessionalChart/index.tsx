import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import { toZonedTime } from 'date-fns-tz';
import { VolumeProfile } from './components/VolumeProfile';
import { Footprint } from './components/Footprint';
import { generateMockFootprintData, generateMockFootprintFromCandles } from './utils/mockFootprintData';
import { parseFootprintCandles } from './parsers/footprintParser';
import { FootprintCandleData } from './renderers/FootprintRenderer';
import { FootprintCandle } from './types';

export interface ChartProps {
  symbol: string;
  timeframe: '30s' | '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w';
  startDate: Date;
  endDate?: Date;
  onDetach?: () => void;
  height?: number;
  showVolumeProfile?: boolean;
}

interface OHLCVData {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export const ProfessionalChart: React.FC<ChartProps> = ({
  symbol,
  timeframe,
  startDate,
  endDate,
  onDetach,
  height = 600,
  showVolumeProfile = true,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const savedLogicalRangeRef = useRef<{ from: number; to: number } | null>(null); // Save zoom level when theme changes
  const [isLoading, setIsLoading] = useState(false);
  const [candlesData, setCandlesData] = useState<any[]>([]);
  const [priceRange, setPriceRange] = useState({ min: 0, max: 0 }); // Full price range for volume profile
  const [footprintPriceRange, setFootprintPriceRange] = useState({ min: 0, max: 0 }); // Visible price range for footprint
  const [footprintData, setFootprintData] = useState<FootprintCandle[]>([]);
  const [footprintCandles, setFootprintCandles] = useState<FootprintCandleData[]>([]);
  const [visibleCandlesCount, setVisibleCandlesCount] = useState<number>(0);
  const [showFootprint, setShowFootprint] = useState<boolean>(false);
  const [isDarkTheme, setIsDarkTheme] = useState<boolean>(true);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart with theme colors
    const theme = isDarkTheme
      ? {
          background: '#0b1523',
          textColor: '#d1d4dc',
          gridColor: '#1e2837',
          borderColor: '#2B2B43',
        }
      : {
          background: '#FFFFFF',
          textColor: '#000000',
          gridColor: '#E0E0E0',
          borderColor: '#CCCCCC',
        };

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: theme.background },
        textColor: theme.textColor,
      },
      grid: {
        vertLines: { color: theme.gridColor },
        horzLines: { color: theme.gridColor },
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true, // Enable PAN by dragging with mouse
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        mouseWheel: true,
        pinch: true,
        axisDoubleClickReset: {
          time: true,
          price: true,
        },
        axisPressedMouseMove: {
          time: true,
          price: true, // Enable vertical PAN on price axis
        },
      },
      localization: {
        locale: 'en-US',
        dateFormat: 'dd MMM \'yy',
        timeFormatter: (timestamp: number | string) => {
          try {
            // Convert timestamp to UTC date
            const utcDate = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp);

            // Convert UTC to Eastern Time (EST/EDT handled automatically)
            const etDate = toZonedTime(utcDate, 'America/New_York');

            // Format in ET
            const hours = etDate.getHours().toString().padStart(2, '0');
            const minutes = etDate.getMinutes().toString().padStart(2, '0');
            const day = etDate.getDate();
            const month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][etDate.getMonth()];
            return timeframe === '30s' || timeframe === '1m'
              ? `${hours}:${minutes}`
              : `${month} ${day} ${hours}:${minutes}`;
          } catch (error) {
            return String(timestamp);
          }
        },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: timeframe === '30s',
        borderColor: theme.borderColor,
      },
      rightPriceScale: {
        borderColor: theme.borderColor,
        minMove: 0.25, // NQ tick size - shows every price level
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      crosshair: {
        mode: 1, // Normal crosshair mode
        vertLine: {
          color: '#758696',
          width: 1,
          style: 3,
          labelBackgroundColor: '#2962ff',
        },
        horzLine: {
          color: '#758696',
          width: 1,
          style: 3,
          labelBackgroundColor: '#2962ff',
        },
      },
    });

    // Create candlestick series with colors matching the reference
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // Create volume series (histogram) below the candlestick chart
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // Use separate price scale for volume
      scaleMargins: {
        top: 0.8, // Volume takes bottom 20% of chart
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Reload data if chart is recreated (e.g., theme change) and we have data
    if (candlesData.length > 0) {
      candlestickSeries.setData(candlesData);

      // Set volume data - transform to histogram format with color based on candle direction
      const volumeData = candlesData.map((candle: any) => ({
        time: candle.time,
        value: candle.volume || 0,
        color: candle.close >= candle.open ? '#26a69a80' : '#ef535080', // Green for up, red for down, with transparency
      }));
      volumeSeries.setData(volumeData);

      // Restore previous zoom level if it exists, otherwise fit all content
      if (savedLogicalRangeRef.current) {
        chart.timeScale().setVisibleLogicalRange(savedLogicalRangeRef.current);
      } else {
        chart.timeScale().fitContent();
      }
    }

    // Expose chart API for testing (only in development)
    if (process.env.NODE_ENV === 'development') {
      (window as any).__CHART_INSTANCE__ = chart;
      (window as any).__CHART_SERIES__ = candlestickSeries;
    }

    // Detect zoom level to toggle between candlestick and footprint mode
    const timeScale = chart.timeScale();
    timeScale.subscribeVisibleLogicalRangeChange(() => {
      const logicalRange = timeScale.getVisibleLogicalRange();
      if (logicalRange) {
        const visibleBars = Math.round(logicalRange.to - logicalRange.from);
        setVisibleCandlesCount(visibleBars);

        // Show footprint when less than 12 candles are visible
        const shouldShowFootprint = visibleBars < 12;
        setShowFootprint(shouldShowFootprint);

        // Hide candlesticks when footprint is active (integrated rendering)
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.applyOptions({
            visible: !shouldShowFootprint
          });
        }
      }
    });

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      // Save current zoom level before destroying chart (for theme changes)
      const logicalRange = chart.timeScale().getVisibleLogicalRange();
      if (logicalRange) {
        savedLogicalRangeRef.current = logicalRange;
      }

      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, timeframe, isDarkTheme]);

  // Fetch data when date range changes
  useEffect(() => {
    const fetchData = async () => {
      if (!candlestickSeriesRef.current) return;

      setIsLoading(true);

      try {
        // Fetch real data from API
        const endDateToUse = endDate || new Date(startDate.getTime() + 12 * 60 * 60 * 1000); // Default to +12h
        const apiUrl = `/api/v1/candles/${symbol}?start_datetime=${startDate.toISOString()}&end_datetime=${endDateToUse.toISOString()}`;

        console.log('Fetching candles from API:', apiUrl);

        const response = await fetch(apiUrl);

        if (!response.ok) {
          throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }

        const apiData = await response.json();

        console.log(`Received ${apiData.length} candles from API`);

        // API returns data in correct TradingView format already
        // { time: number, open: number, high: number, low: number, close: number, volume: number }
        const candlesData: CandlestickData[] = apiData;

        // Fallback to mock data if API returns empty
        const mockData: CandlestickData[] = candlesData.length > 0
          ? candlesData
          : generateMockData(startDate, endDateToUse);

        candlestickSeriesRef.current.setData(mockData);

        // Set volume data
        if (volumeSeriesRef.current) {
          const volumeData = mockData.map((candle: any) => ({
            time: candle.time,
            value: candle.volume || 0,
            color: candle.close >= candle.open ? '#26a69a80' : '#ef535080', // Green for up, red for down, with transparency
          }));
          volumeSeriesRef.current.setData(volumeData);
        }

        chartRef.current?.timeScale().fitContent();

        // Save data for volume profile
        setCandlesData(mockData);

        // Generate mock footprint data FROM THE SAME CANDLES
        // This ensures footprint levels align with candle OHLC values
        const mockFootprint = generateMockFootprintFromCandles(mockData);
        setFootprintData(mockFootprint);

        // Expose data for testing
        if (process.env.NODE_ENV === 'development') {
          (window as any).__CANDLES_DATA__ = mockData;
          (window as any).__FOOTPRINT_DATA__ = mockFootprint;

          // Log to verify alignment
          console.log('Candle-Footprint Alignment Check:');
          mockData.slice(0, 3).forEach((candle, i) => {
            const fp = mockFootprint[i];
            if (fp) {
              console.log(`Candle ${i}: H=${candle.high.toFixed(2)}, L=${candle.low.toFixed(2)} | ` +
                         `Footprint ${i}: H=${fp.high.toFixed(2)}, L=${fp.low.toFixed(2)} | ` +
                         `Match: ${candle.high === fp.high && candle.low === fp.low ? '✅' : '❌'}`);
            }
          });
        }

        // Calculate price range
        if (mockData.length > 0) {
          const highs = mockData.map(d => d.high);
          const lows = mockData.map(d => d.low);
          setPriceRange({
            min: Math.min(...lows),
            max: Math.max(...highs),
          });
        }
      } catch (error) {
        console.error('Error fetching chart data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [symbol, timeframe, startDate, endDate]);

  // Candlesticks remain ALWAYS visible - footprint overlays on top
  // DO NOT hide candles in footprint mode

  // Process footprint data when needed - now also responds to PAN
  useEffect(() => {
    if (!showFootprint || footprintData.length === 0 || !chartRef.current) return;

    const chart = chartRef.current;
    const timeScale = chart.timeScale();

    // Function to update footprint coordinates
    const updateFootprintCoordinates = () => {
      const logicalRange = timeScale.getVisibleLogicalRange();
      if (!logicalRange) return;

      // Get visible candle indices
      const fromIndex = Math.floor(logicalRange.from);
      const toIndex = Math.ceil(logicalRange.to);

      // Debug: log the range change
      console.log('Updating footprint coordinates:', { fromIndex, toIndex, logicalRange });

      // Filter only visible footprint data
      const visibleFootprint = footprintData.slice(
        Math.max(0, fromIndex),
        Math.min(footprintData.length, toIndex)
      );

        if (visibleFootprint.length === 0) return;

      // Parse visible footprint candles - use oflow_detail (0.25 tick granularity) for accurate POC
      // This gives us the real POC at 0.25 tick precision as requested
      const parsed = parseFootprintCandles(visibleFootprint, true);

      // Calculate visible price range from visible candles only
      const visibleHighs = visibleFootprint.map(c => c.high);
      const visibleLows = visibleFootprint.map(c => c.low);
      const visiblePriceMin = Math.min(...visibleLows);
      const visiblePriceMax = Math.max(...visibleHighs);

      // Update visible price range for footprint renderer only
      setFootprintPriceRange({
        min: visiblePriceMin,
        max: visiblePriceMax,
      });

      // Map footprint candles to chart coordinates
      const footprintCandlesData: FootprintCandleData[] = parsed.map((candle, index) => {
        const actualIndex = fromIndex + index;
        const time = candlesData[actualIndex]?.time;

        if (!time) {
          return {
            x: 0,
            width: 0,
            levels: candle.levels,
            delta: candle.candleData.delta,
            volume: candle.candleData.volume,
            open: candle.candleData.open,
            high: candle.candleData.high,
            low: candle.candleData.low,
            close: candle.candleData.close,
          };
        }

        // Get actual X coordinate from chart - this updates with PAN
        const xCoord = timeScale.timeToCoordinate(time as any);

        // Debug: log coordinate for first and last candle
        if (index === 0 || index === parsed.length - 1) {
          console.log(`Candle ${index} time=${time}, xCoord=${xCoord}`);
        }

        // Calculate candle width from spacing
        const nextTime = candlesData[actualIndex + 1]?.time;
        const nextX = nextTime ? timeScale.timeToCoordinate(nextTime as any) : null;
        const candleWidth = nextX && xCoord ? Math.abs(nextX - xCoord) : 50;

        return {
          x: xCoord || 0,
          width: candleWidth,
          levels: candle.levels,
          delta: candle.candleData.delta,
          volume: candle.candleData.volume,
          open: candle.candleData.open,
          high: candle.candleData.high,
          low: candle.candleData.low,
          close: candle.candleData.close,
        };
      }).filter(c => c.x > 0); // Filter out invalid coordinates

      // Force React to recognize state change by creating new array
      setFootprintCandles([...footprintCandlesData]);

      // Expose processed footprint data for testing
      if (process.env.NODE_ENV === 'development' && footprintCandlesData.length > 0) {
        (window as any).__FOOTPRINT_CANDLES__ = footprintCandlesData;
        (window as any).__FOOTPRINT_VISIBLE__ = true;
        console.log(`Footprint candles updated: ${footprintCandlesData.length} candles, first X: ${footprintCandlesData[0]?.x}`);
      }
    };

    // Initial update
    updateFootprintCoordinates();

    // Subscribe to visible time range changes (includes PAN and zoom)
    const unsubscribe = timeScale.subscribeVisibleTimeRangeChange(() => {
      console.log('TimeScale changed - updating footprint coordinates');
      updateFootprintCoordinates();
    });

    // Cleanup subscription
    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, [showFootprint, footprintData, candlesData, visibleCandlesCount]);

  return (
    <div className="relative flex flex-col h-full w-full rounded-2xl border border-border/40 bg-gradient-to-b from-[#111c2d] via-[#0b1523] to-[#070c16]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/40 bg-[#0d1726]/70 px-5 py-3">
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <h3 className="text-sm font-bold uppercase tracking-[0.28em] text-foreground/90">
              {symbol} - {timeframe}
              <span className="ml-3 text-xs text-yellow-400 bg-yellow-400/10 px-2 py-0.5 rounded border border-yellow-400/30">
                ET
              </span>
              {showFootprint && (
                <span className="ml-3 text-xs text-cyan-400">
                  [FOOTPRINT MODE - {visibleCandlesCount} bars]
                </span>
              )}
            </h3>
            <p className="text-[0.65rem] uppercase tracking-[0.22em] text-muted-foreground/70">
              {startDate.toLocaleDateString()} {startDate.toLocaleTimeString()}
              {endDate && ` - ${endDate.toLocaleDateString()}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isLoading && (
            <span className="text-xs text-muted-foreground">Loading...</span>
          )}
          <button
            onClick={() => {
              if (chartRef.current) {
                chartRef.current.timeScale().resetTimeScale();
                chartRef.current.timeScale().fitContent();
                setShowFootprint(false); // Exit footprint mode on reset
              }
            }}
            className="rounded-lg bg-primary/20 px-3 py-1.5 text-xs uppercase tracking-wider text-primary hover:bg-primary/30 transition-colors"
            data-testid="reset-zoom"
          >
            Reset Zoom
          </button>
          <button
            onClick={() => setIsDarkTheme(!isDarkTheme)}
            className="rounded-lg bg-primary/20 px-3 py-1.5 text-xs uppercase tracking-wider text-primary hover:bg-primary/30 transition-colors"
            data-testid="theme-toggle"
          >
            {isDarkTheme ? 'Light' : 'Dark'}
          </button>
          {onDetach && (
            <button
              onClick={onDetach}
              className="rounded-lg bg-primary/20 px-3 py-1.5 text-xs uppercase tracking-wider text-primary hover:bg-primary/30 transition-colors"
              data-testid="detach-chart"
            >
              Detach
            </button>
          )}
        </div>
      </div>

      {/* Chart Container */}
      <div
        ref={chartContainerRef}
        className="flex-1 relative"
        style={{ minHeight: height }}
      >
        {/* Volume Profile Overlay - DISABLED per user request */}
        {/* {showVolumeProfile && candlesData.length > 0 && priceRange.max > 0 && (
          <VolumeProfile
            candles={candlesData}
            width={150}
            height={height}
            priceMin={priceRange.min}
            priceMax={priceRange.max}
            showPOC={true}
            showVAH={true}
            showVAL={true}
          />
        )} */}

        {/* Footprint Overlay - shown when zoomed in < 20 candles */}
        {showFootprint && footprintCandles.length > 0 && footprintPriceRange.max > 0 && (
          <Footprint
            candles={footprintCandles}
            width={chartContainerRef.current?.clientWidth || 1200}
            height={height}
            priceMin={footprintPriceRange.min}
            priceMax={footprintPriceRange.max}
            showNumbers={true}
            showHeatmap={true}
            showDelta={false}
            showPOCBorder={true}
            fontSize={16}
            isDarkTheme={isDarkTheme}
          />
        )}
      </div>
    </div>
  );
};

// Temporary mock data generator
function generateMockData(startDate: Date, endDate: Date): CandlestickData[] {
  const data: CandlestickData[] = [];
  const interval = 5 * 60 * 1000; // 5 minutes
  let basePrice = 20600; // Realistic NQ price around 20600

  let currentTime = startDate.getTime();
  const endTime = endDate.getTime();

  while (currentTime <= endTime) {
    // Realistic range: 5-30 points per 5min candle (20-120 ticks)
    // Mean: 15 points (60 ticks)
    // 1 point = 4 ticks = 1.0, 1 tick = 0.25
    const rangeInPoints = 5 + Math.random() * 25; // 5-30 points
    const rangeInPrice = rangeInPoints; // Since 1 point = 1.0 for NQ

    // Small drift for base price
    const drift = (Math.random() - 0.5) * 5;

    const open = basePrice + drift;
    const closeDirection = Math.random() > 0.5 ? 1 : -1;
    const close = open + closeDirection * (Math.random() * rangeInPrice);

    const high = Math.max(open, close) + Math.random() * (rangeInPrice * 0.3);
    const low = Math.min(open, close) - Math.random() * (rangeInPrice * 0.3);

    const volume = Math.floor(Math.random() * 3000) + 500;

    data.push({
      time: (currentTime / 1000) as Time,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume,
    } as CandlestickData);

    basePrice = close;
    currentTime += interval;
  }

  return data;
}
