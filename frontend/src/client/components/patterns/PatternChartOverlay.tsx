import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Line } from 'recharts';
import type { FVGPattern, OrderBlockPattern, LiquidityPoolPattern } from '@/hooks/usePatterns';

export interface CandleData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PatternChartOverlayProps {
  candles: CandleData[];
  fvgs?: FVGPattern[];
  orderBlocks?: OrderBlockPattern[];
  liquidityPools?: LiquidityPoolPattern[];
}

const FVG_BULLISH_COLOR = '#3b82f680';
const FVG_BEARISH_COLOR = '#ef444480';
const OB_COLOR = '#f9731680';
const LP_COLOR = '#8b5cf6';

export function PatternChartOverlay({
  candles,
  fvgs = [],
  orderBlocks = [],
  liquidityPools = [],
}: PatternChartOverlayProps) {
  if (candles.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-500">
        No chart data available
      </div>
    );
  }

  // Prepare candle data for recharts
  const chartData = candles.map((candle) => ({
    ...candle,
    time: new Date(candle.timestamp).toLocaleTimeString(),
  }));

  return (
    <div className="w-full h-96 bg-white p-4 rounded-lg border border-gray-200">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />

          {/* Render FVG zones */}
          {fvgs.map((fvg, index) => (
            <ReferenceArea
              key={`fvg-${index}`}
              y1={fvg.bottom}
              y2={fvg.top}
              fill={fvg.direction === 'bullish' ? FVG_BULLISH_COLOR : FVG_BEARISH_COLOR}
              fillOpacity={0.5}
              ifOverflow="extendDomain"
            />
          ))}

          {/* Render Order Block zones */}
          {orderBlocks.map((ob, index) => (
            <ReferenceArea
              key={`ob-${index}`}
              y1={ob.bottom}
              y2={ob.top}
              fill={OB_COLOR}
              fillOpacity={0.5}
              ifOverflow="extendDomain"
            />
          ))}

          {/* Render Liquidity Pool lines */}
          {liquidityPools.map((lp, index) => (
            <Line
              key={`lp-${index}`}
              type="monotone"
              dataKey={() => lp.price}
              stroke={LP_COLOR}
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          ))}

          {/* Render candlesticks */}
          <Line
            type="monotone"
            dataKey="high"
            stroke="#000"
            strokeWidth={1}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="low"
            stroke="#000"
            strokeWidth={1}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="open"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}