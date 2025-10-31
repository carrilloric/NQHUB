import React, { useEffect, useRef } from "react";
import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { OHLCVCandle } from "@shared/mock-data";

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
    <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl border border-border/40 bg-gradient-to-b from-[#111c2d] via-[#0b1523] to-[#070c16]">
      <div className="flex items-center justify-between border-b border-border/40 bg-[#0d1726]/70 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-full border border-primary/40 bg-primary/15 p-2">
            <TrendingUp className="size-4 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-[0.28em] text-foreground/90">{title}</h3>
            <p className="text-[0.65rem] uppercase tracking-[0.22em] text-muted-foreground/70">
              {data.length} candles • {(highPrice - lowPrice).toFixed(2)} range
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-lg font-semibold text-foreground/95">{lastCandle.close.toFixed(2)}</p>
          <p className={cn("text-sm font-semibold", priceChange >= 0 ? "text-bullish" : "text-bearish")}>
            {priceChange >= 0 ? "+" : ""}
            {priceChange.toFixed(2)} ({percentChange}%)
          </p>
        </div>
      </div>

      <div
        ref={containerRef}
        style={{ height: `calc(100% - 100px)` }}
        className="relative flex-1 bg-[radial-gradient(circle_at_center,_rgba(23,211,218,0.08),_transparent)]"
      >
        <div className="absolute inset-0 flex items-center justify-center text-muted-foreground/70">
          <div className="text-center space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.28em] text-foreground/75">SciChart Integration Ready</p>
            <p className="text-xs uppercase tracking-[0.24em]">
              Install <code className="rounded bg-primary/20 px-2 py-1 text-primary">npm install scichart</code>
            </p>
            <p className="text-xs text-muted-foreground/70 uppercase tracking-[0.24em]">
              Chart will render with {data.length} candles
            </p>
          </div>
        </div>
        {/* SciChart will render here once installed and configured */}
      </div>

      <div className="border-t border-border/40 bg-[#0d1726]/70 px-5 py-3 text-[0.7rem] uppercase tracking-[0.24em] text-muted-foreground/75">
        <div className="grid grid-cols-5 gap-2">
          <div>
            <span className="text-muted-foreground/60">O:</span> {lastCandle.open.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground/60">H:</span> {lastCandle.high.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground/60">L:</span> {lastCandle.low.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground/60">C:</span> {lastCandle.close.toFixed(2)}
          </div>
          <div>
            <span className="text-muted-foreground/60">V:</span> {(lastCandle.volume / 1000000).toFixed(1)}M
          </div>
        </div>
      </div>
    </div>
  );
};
