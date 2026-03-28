/**
 * Candlestick Chart Component
 *
 * Uses lightweight-charts to display price action with SMC overlays
 */

import React, { useRef, useEffect, useState } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';

interface CandlestickChartProps {
  timeframe: string;
  priceData: any;
  patterns?: any;
}

export default function CandlestickChart({ timeframe, priceData, patterns }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up previous chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    // Create chart
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: 'transparent' },
        textColor: '#888',
      },
      grid: {
        vertLines: { color: '#2a2a2a20' },
        horzLines: { color: '#2a2a2a20' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#2a2a2a20',
      },
      timeScale: {
        borderColor: '#2a2a2a20',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    candleSeriesRef.current = candleSeries;

    // Generate mock candlestick data
    const currentTime = Math.floor(Date.now() / 1000);
    const mockCandles = [];
    let basePrice = 20150;

    for (let i = 100; i >= 0; i--) {
      const time = currentTime - i * (timeframe === '1min' ? 60 : timeframe === '5min' ? 300 : 900);
      const open = basePrice + (Math.random() - 0.5) * 10;
      const close = open + (Math.random() - 0.5) * 15;
      const high = Math.max(open, close) + Math.random() * 5;
      const low = Math.min(open, close) - Math.random() * 5;

      mockCandles.push({
        time: time,
        open: open,
        high: high,
        low: low,
        close: close,
      });

      basePrice = close;
    }

    candleSeries.setData(mockCandles);

    // Add FVG zones (Fair Value Gaps) as price lines
    if (patterns && patterns.pattern_type === 'FVG') {
      const fvgHigh = chart.addLineSeries({
        color: 'rgba(16, 185, 129, 0.3)',
        lineWidth: 0,
        priceLineVisible: false,
      });

      const fvgLow = chart.addLineSeries({
        color: 'rgba(239, 68, 68, 0.3)',
        lineWidth: 0,
        priceLineVisible: false,
      });

      // Add sample FVG zone
      const fvgData = [
        { time: currentTime - 50 * 60, value: 20160 },
        { time: currentTime - 40 * 60, value: 20160 },
      ];
      fvgHigh.setData(fvgData);

      const fvgLowData = [
        { time: currentTime - 50 * 60, value: 20155 },
        { time: currentTime - 40 * 60, value: 20155 },
      ];
      fvgLow.setData(fvgLowData);
    }

    // Add Order Block zones
    const orderBlockSeries = chart.addHistogramSeries({
      color: 'rgba(59, 130, 246, 0.2)',
      priceFormat: {
        type: 'volume',
      },
    });

    // Sample order block
    const orderBlockData = [
      { time: currentTime - 70 * 60, value: 50, color: 'rgba(59, 130, 246, 0.3)' },
      { time: currentTime - 69 * 60, value: 50, color: 'rgba(59, 130, 246, 0.3)' },
      { time: currentTime - 68 * 60, value: 50, color: 'rgba(59, 130, 246, 0.3)' },
    ];
    orderBlockSeries.setData(orderBlockData);

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Update with real-time price data if available
    if (priceData) {
      const newCandle = {
        time: Math.floor(Date.now() / 1000),
        open: priceData.bid || basePrice,
        high: priceData.ask || basePrice + 1,
        low: priceData.bid || basePrice,
        close: priceData.last || basePrice,
      };
      candleSeries.update(newCandle);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [timeframe, priceData, patterns]);

  return (
    <div className="w-full">
      <div ref={containerRef} className="chart-container" />

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500/30 rounded"></div>
          <span>FVG (Bullish)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500/30 rounded"></div>
          <span>FVG (Bearish)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500/30 rounded"></div>
          <span>Order Block</span>
        </div>
      </div>
    </div>
  );
}