import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { format } from 'date-fns';

interface EquityDataPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
}

interface EquityCurveChartProps {
  data: EquityDataPoint[];
  initialCapital?: number;
  showDrawdown?: boolean;
  className?: string;
}

export function EquityCurveChart({
  data,
  initialCapital = 25000,
  showDrawdown = true,
  className,
}: EquityCurveChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Equity Curve</CardTitle>
          <CardDescription>No data available</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Format data for recharts
  const chartData = data.map((point) => ({
    ...point,
    date: format(new Date(point.timestamp), 'MMM dd'),
    drawdownPercent: point.drawdown * 100,
  }));

  const maxEquity = Math.max(...data.map((d) => d.equity));
  const minEquity = Math.min(...data.map((d) => d.equity));
  const finalEquity = data[data.length - 1].equity;
  const totalReturn = ((finalEquity - initialCapital) / initialCapital) * 100;
  const maxDrawdown = Math.min(...data.map((d) => d.drawdown)) * 100;

  const formatYAxis = (value: number) => {
    return `$${(value / 1000).toFixed(0)}k`;
  };

  const formatTooltipValue = (value: number, name: string) => {
    if (name === 'Drawdown') {
      return `${value.toFixed(2)}%`;
    }
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <Card className={className} data-testid="equity-curve-chart">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Equity Curve</CardTitle>
            <CardDescription>Portfolio value over time</CardDescription>
          </div>
          <div className="flex gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Return:</span>
              <span
                className={`ml-1 font-semibold ${
                  totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Max DD:</span>
              <span className="ml-1 font-semibold text-red-600">
                {maxDrawdown.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          {showDrawdown ? (
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
              <XAxis
                dataKey="date"
                stroke="#888"
                fontSize={12}
                interval="preserveStartEnd"
              />
              <YAxis
                yAxisId="equity"
                stroke="#888"
                fontSize={12}
                tickFormatter={formatYAxis}
                domain={[minEquity * 0.98, maxEquity * 1.02]}
              />
              <YAxis
                yAxisId="drawdown"
                orientation="right"
                stroke="#888"
                fontSize={12}
                tickFormatter={(value) => `${value}%`}
                domain={[maxDrawdown * 1.2, 0]}
              />
              <Tooltip
                formatter={formatTooltipValue}
                labelFormatter={(label) => `Date: ${label}`}
                contentStyle={{
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  border: '1px solid #333',
                  borderRadius: '4px',
                }}
              />
              <Legend />
              <ReferenceLine
                yAxisId="equity"
                y={initialCapital}
                stroke="#666"
                strokeDasharray="5 5"
                label={{ value: 'Initial Capital', position: 'left' }}
              />
              <ReferenceLine
                yAxisId="drawdown"
                y={0}
                stroke="#666"
                strokeDasharray="5 5"
              />
              <Area
                yAxisId="drawdown"
                type="monotone"
                dataKey="drawdownPercent"
                stroke="none"
                fill="#ef4444"
                fillOpacity={0.3}
                name="Drawdown"
              />
              <Line
                yAxisId="equity"
                type="monotone"
                dataKey="equity"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
                name="Equity"
              />
            </ComposedChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
              <XAxis
                dataKey="date"
                stroke="#888"
                fontSize={12}
                interval="preserveStartEnd"
              />
              <YAxis
                stroke="#888"
                fontSize={12}
                tickFormatter={formatYAxis}
                domain={[minEquity * 0.98, maxEquity * 1.02]}
              />
              <Tooltip
                formatter={formatTooltipValue}
                labelFormatter={(label) => `Date: ${label}`}
                contentStyle={{
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  border: '1px solid #333',
                  borderRadius: '4px',
                }}
              />
              <Legend />
              <ReferenceLine
                y={initialCapital}
                stroke="#666"
                strokeDasharray="5 5"
                label={{ value: 'Initial Capital', position: 'left' }}
              />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
                name="Equity"
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}