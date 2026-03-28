/**
 * Comparison View Component
 * Compare multiple backtest runs side by side
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { X, TrendingUp, TrendingDown } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface BacktestRun {
  id: string;
  strategy_id: string;
  strategy_name: string;
  status: string;
  start_date: string;
  end_date: string;
  symbol: string;
  timeframe: string;
  results?: {
    sharpe: number;
    profit_factor: number;
    total_trades: number;
    win_rate: number;
    max_dd: number;
    total_pnl: number;
    avg_win: number;
    avg_loss: number;
    equity_curve: Array<{
      timestamp: string;
      balance: number;
    }>;
  };
}

interface ComparisonViewProps {
  runs: BacktestRun[];
  onRemove: (id: string) => void;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ runs, onRemove }) => {
  if (runs.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <p className="text-muted-foreground">No runs selected for comparison</p>
            <p className="text-sm text-muted-foreground">
              Select 2-5 backtest runs to compare performance
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare equity curve data for chart
  const chartData = prepareChartData(runs);

  // Define comparison metrics
  const metrics = [
    { key: 'total_pnl', label: 'Total P&L', format: 'currency' },
    { key: 'sharpe', label: 'Sharpe Ratio', format: 'ratio' },
    { key: 'profit_factor', label: 'Profit Factor', format: 'ratio' },
    { key: 'win_rate', label: 'Win Rate', format: 'percent' },
    { key: 'max_dd', label: 'Max Drawdown', format: 'percent' },
    { key: 'total_trades', label: 'Total Trades', format: 'number' },
    { key: 'avg_win', label: 'Avg Win', format: 'currency' },
    { key: 'avg_loss', label: 'Avg Loss', format: 'currency' },
  ];

  const formatValue = (value: number | undefined, format: string): string => {
    if (value === undefined) return 'N/A';

    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'percent':
        return `${(value * 100).toFixed(2)}%`;
      case 'ratio':
        return value.toFixed(2);
      default:
        return value.toLocaleString();
    }
  };

  const getBestValue = (metric: string, runs: BacktestRun[]): string => {
    const values = runs
      .filter(r => r.results)
      .map(r => r.results![metric as keyof typeof r.results]);

    if (values.length === 0) return '';

    const numericValues = values.filter(v => typeof v === 'number') as number[];
    if (numericValues.length === 0) return '';

    const bestValue = metric === 'max_dd'
      ? Math.max(...numericValues)
      : Math.max(...numericValues);

    return runs.find(r => r.results?.[metric as keyof typeof r.results] === bestValue)?.id || '';
  };

  // Color palette for chart lines
  const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Selected Runs */}
      <Card>
        <CardHeader>
          <CardTitle>Selected Runs</CardTitle>
          <CardDescription>
            Comparing {runs.length} backtest run{runs.length > 1 ? 's' : ''}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {runs.map((run, index) => (
              <Badge
                key={run.id}
                variant="secondary"
                className="pl-3 pr-1 py-1"
              >
                <span
                  className="w-2 h-2 rounded-full mr-2"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                {run.strategy_name}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 ml-2 hover:bg-transparent"
                  onClick={() => onRemove(run.id)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Equity Curve Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Equity Curve Comparison</CardTitle>
          <CardDescription>
            Normalized equity curves for visual comparison
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="index"
                  label={{ value: 'Trade Number', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  label={{ value: 'Normalized Balance', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: number) => value.toFixed(2)}
                  labelFormatter={(label) => `Trade #${label}`}
                />
                <Legend />
                {runs.map((run, index) => (
                  <Line
                    key={run.id}
                    type="monotone"
                    dataKey={run.id}
                    name={run.strategy_name}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Metrics Comparison</CardTitle>
          <CardDescription>
            Side-by-side comparison of key performance metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  {runs.map((run) => (
                    <TableHead key={run.id} className="text-center">
                      <div className="space-y-1">
                        <div>{run.strategy_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {run.symbol} • {run.timeframe}
                        </div>
                      </div>
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {metrics.map((metric) => {
                  const bestRunId = getBestValue(metric.key, runs);

                  return (
                    <TableRow key={metric.key}>
                      <TableCell className="font-medium">
                        {metric.label}
                      </TableCell>
                      {runs.map((run) => {
                        const value = run.results?.[metric.key as keyof typeof run.results];
                        const isBest = run.id === bestRunId;
                        const isDrawdown = metric.key === 'max_dd';
                        const isLoss = metric.key === 'avg_loss';

                        return (
                          <TableCell
                            key={run.id}
                            className={cn(
                              'text-center',
                              isBest && !isDrawdown && !isLoss && 'font-bold text-green-500',
                              isBest && (isDrawdown || isLoss) && 'font-bold text-blue-500'
                            )}
                          >
                            <div className="flex items-center justify-center gap-1">
                              {formatValue(value as number, metric.format)}
                              {isBest && (
                                isDrawdown || isLoss ? (
                                  <TrendingUp className="h-3 w-3" />
                                ) : (
                                  <TrendingUp className="h-3 w-3" />
                                )
                              )}
                            </div>
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {runs.map((run, index) => {
              if (!run.results) return null;

              const rank = calculateRank(run, runs);

              return (
                <div
                  key={run.id}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: colors[index % colors.length] }}
                    />
                    <div>
                      <div className="font-medium">{run.strategy_name}</div>
                      <div className="text-sm text-muted-foreground">
                        {format(new Date(run.start_date), 'MMM d')} - {format(new Date(run.end_date), 'MMM d, yyyy')}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant={rank === 1 ? 'default' : 'secondary'}>
                      Rank #{rank}
                    </Badge>
                    <div className={cn(
                      'font-bold',
                      run.results.total_pnl > 0 ? 'text-green-500' : 'text-red-500'
                    )}>
                      {formatValue(run.results.total_pnl, 'currency')}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Helper function to prepare chart data
function prepareChartData(runs: BacktestRun[]) {
  // Find the maximum number of points
  const maxPoints = Math.max(
    ...runs.map(r => r.results?.equity_curve?.length || 0)
  );

  // Create normalized data
  const data = [];
  for (let i = 0; i < maxPoints; i++) {
    const point: any = { index: i };

    runs.forEach(run => {
      if (run.results?.equity_curve && run.results.equity_curve[i]) {
        const initialBalance = run.results.equity_curve[0].balance;
        const normalizedBalance = (run.results.equity_curve[i].balance / initialBalance) * 100;
        point[run.id] = normalizedBalance;
      }
    });

    data.push(point);
  }

  return data;
}

// Helper function to calculate rank
function calculateRank(run: BacktestRun, allRuns: BacktestRun[]): number {
  const scores = allRuns.map(r => {
    if (!r.results) return { id: r.id, score: -Infinity };

    // Simple scoring based on Sharpe and total P&L
    const score = (r.results.sharpe * 1000) + (r.results.total_pnl / 100);
    return { id: r.id, score };
  });

  scores.sort((a, b) => b.score - a.score);
  const rank = scores.findIndex(s => s.id === run.id) + 1;

  return rank;
}