/**
 * CandlestickChart Component
 *
 * Recharts-based candlestick chart with SMC pattern overlays:
 * - FVG zones (blue ReferenceArea)
 * - OB zones (orange ReferenceArea)
 * - LP lines (purple ReferenceLine)
 *
 * Updates in real-time via WebSocket (price + patterns channels).
 */
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
} from 'recharts';
import type { CandleEvent, PatternEvent } from '@/stores/websocketStore';

interface CandlestickChartProps {
  candles: CandleEvent[];
  patterns: PatternEvent[];
}

interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  color: string;
}

export function CandlestickChart({ candles, patterns }: CandlestickChartProps) {
  // Transform candles for recharts
  const chartData: CandleData[] = candles.slice(-50).map((candle) => ({
    time: new Date(candle.ts).toLocaleTimeString(),
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    color: candle.close >= candle.open ? '#10b981' : '#ef4444',
  }));

  // Filter patterns for overlays
  const fvgs = patterns.filter((p) => p.pattern_type === 'fvg');
  const obs = patterns.filter((p) => p.pattern_type === 'ob');
  const lps = patterns.filter((p) => p.pattern_type === 'lp');

  if (chartData.length === 0) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg border bg-white">
        <p className="text-gray-500">No candle data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-6" data-testid="candlestick-chart">
      <h3 className="mb-4 text-lg font-semibold">NQ 1-Minute Chart</h3>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <XAxis dataKey="time" tick={{ fontSize: 12 }} />
          <YAxis domain={['dataMin - 10', 'dataMax + 10']} tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
            formatter={(value: number) => `$${value.toFixed(2)}`}
          />

          {/* FVG Zones (blue semi-transparent) */}
          {fvgs.map((fvg, idx) => (
            <ReferenceArea
              key={`fvg-${idx}`}
              y1={fvg.top}
              y2={fvg.bottom}
              fill="#3b82f6"
              fillOpacity={0.2}
              stroke="#3b82f6"
              strokeDasharray="3 3"
            />
          ))}

          {/* Order Block Zones (orange semi-transparent) */}
          {obs.map((ob, idx) => (
            <ReferenceArea
              key={`ob-${idx}`}
              y1={ob.top}
              y2={ob.bottom}
              fill="#f97316"
              fillOpacity={0.2}
              stroke="#f97316"
              strokeDasharray="3 3"
            />
          ))}

          {/* Liquidity Pool Lines (purple) */}
          {lps.map((lp, idx) => (
            <ReferenceLine
              key={`lp-${idx}`}
              y={lp.top}
              stroke="#a855f7"
              strokeWidth={2}
              strokeDasharray="5 5"
            />
          ))}

          {/* Candlestick bars */}
          <Bar dataKey="close" fill="#8884d8" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
