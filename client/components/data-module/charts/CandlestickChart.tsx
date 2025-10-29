import React, { useEffect, useRef } from "react";
import { TrendingUp } from "lucide-react";
import type { OHLCVCandle } from "@/shared/mock-data";

/**
 * INSTALLATION REQUIRED:
 * Run: npm install scichart
 * 
 * This component uses SciChart for professional candlestick charting.
 * Replace the mock rendering with actual SciChart initialization.
 */

interface CandlestickChartProps {
  data: OHLCVCandle[];
  title?: string;
  height?: number;
  showVolume?: boolean;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  title = "Candlestick Chart",
  height = 400,
  showVolume = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;

    // TODO: Replace this mock rendering with SciChart initialization
    // 
    // const { SciChartSurface, NumericAxis, DateTimeAxis, OhlcDataSeries, CandlestickRenderableSeries } = require('scichart');
    // 
    // const initChart = async () => {
    //   const { sciChartSurface, wasmContext } = await SciChartSurface.create(containerRef.current!);
    //   
    //   const xAxis = new DateTimeAxis(wasmContext);
    //   const yAxis = new NumericAxis(wasmContext);
    //   
    //   const dataSeries = new OhlcDataSeries(wasmContext);
    //   dataSeries.appendRange(
    //     data.map(d => d.timestamp),
    //     data.map(d => d.open),
    //     data.map(d => d.high),
    //     data.map(d => d.low),
    //     data.map(d => d.close)
    //   );
    //   
    //   const series = new CandlestickRenderableSeries(wasmContext, {
    //     dataSeries,
    //     strokeUp: "#26a69a",
    //     strokeDown: "#ef5350"
    //   });
    //   
    //   sciChartSurface.xAxes.add(xAxis);
    //   sciChartSurface.yAxes.add(yAxis);
    //   sciChartSurface.renderableSeries.add(series);
    // };
    // 
    // initChart();
  }, [data]);

  const highPrice = Math.max(...data.map((d) => d.high));
  const lowPrice = Math.min(...data.map((d) => d.low));
  const lastCandle = data[data.length - 1];
  const priceChange = lastCandle.close - lastCandle.open;
  const percentChange = ((priceChange / lastCandle.open) * 100).toFixed(2);

  return (
    <div className="w-full h-full flex flex-col bg-card rounded-lg border border-border overflow-hidden">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-4 text-primary" />
          <div>
            <h3 className="font-semibold">{title}</h3>
            <p className="text-xs text-muted-foreground">
              {data.length} candles • {(highPrice - lowPrice).toFixed(2)} range
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="font-semibold text-lg">{lastCandle.close.toFixed(2)}</p>
          <p className={`text-sm ${priceChange >= 0 ? "text-green-600" : "text-red-600"}`}>
            {priceChange >= 0 ? "+" : ""}{priceChange.toFixed(2)} ({percentChange}%)
          </p>
        </div>
      </div>

      <div
        ref={containerRef}
        style={{ height: `calc(100% - 80px)` }}
        className="flex-1 relative bg-gradient-to-b from-background to-background/50"
      >
        <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
          <div className="text-center">
            <p className="text-sm font-medium mb-2">SciChart Integration Ready</p>
            <p className="text-xs">
              Install: <code className="bg-accent px-2 py-1 rounded">npm install scichart</code>
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Chart will render with {data.length} candles
            </p>
          </div>
        </div>

        {/* SciChart will render here once installed and configured */}
      </div>

      <div className="p-3 border-t border-border text-xs text-muted-foreground">
        <div className="grid grid-cols-5 gap-2">
          <div>
            <span className="text-muted-foreground">O:</span> {lastCandle.open.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground">H:</span> {lastCandle.high.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground">L:</span> {lastCandle.low.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground">C:</span> {lastCandle.close.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground">V:</span> {(lastCandle.volume / 1000000).toFixed(1)}M
          </div>
        </div>
      </div>
    </div>
  );
};
