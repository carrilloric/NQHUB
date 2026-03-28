/**
 * Backtest Results Component
 * Displays comprehensive backtest results including metrics, equity curve, and trade list
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  FileText,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface BacktestRun {
  id: string;
  strategy_id: string;
  strategy_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  start_date: string;
  end_date: string;
  symbol: string;
  timeframe: string;
  created_at: string;
  completed_at?: string;
  duration_seconds?: number;
  results?: {
    sharpe: number;
    profit_factor: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    max_dd: number;
    total_pnl: number;
    avg_win: number;
    avg_loss: number;
    best_trade: number;
    worst_trade: number;
    max_consecutive_wins: number;
    max_consecutive_losses: number;
    equity_curve: Array<{
      timestamp: string;
      balance: number;
      drawdown: number;
    }>;
    trades: Array<{
      id: string;
      symbol: string;
      side: 'long' | 'short';
      entry_time: string;
      exit_time: string;
      entry_price: number;
      exit_price: number;
      quantity: number;
      pnl: number;
      pnl_percent: number;
      commission: number;
      slippage: number;
      tags: string[];
    }>;
  };
}

interface BacktestResultsProps {
  run?: BacktestRun;
}

export const BacktestResults: React.FC<BacktestResultsProps> = ({ run }) => {
  const [selectedTab, setSelectedTab] = useState('overview');

  if (!run) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto" />
            <p className="text-muted-foreground">No backtest results to display</p>
            <p className="text-sm text-muted-foreground">
              Run a backtest to see performance metrics
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Check if run is still processing
  if (run.status === 'pending' || run.status === 'running') {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
            <p className="font-medium">Backtest {run.status === 'pending' ? 'Pending' : 'Running'}...</p>
            <p className="text-sm text-muted-foreground">
              This may take a few moments
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Check for failed status
  if (run.status === 'failed' || !run.results) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
            <p className="font-medium text-destructive">Backtest Failed</p>
            <p className="text-sm text-muted-foreground">
              There was an error running the backtest
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { results } = run;

  // Format metrics for display
  const formatMetric = (value: number, type: 'percent' | 'currency' | 'number' | 'ratio' = 'number') => {
    switch (type) {
      case 'percent':
        return `${(value * 100).toFixed(2)}%`;
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'ratio':
        return value.toFixed(2);
      default:
        return value.toLocaleString();
    }
  };

  // Metric cards data
  const metricCards = [
    {
      title: 'Total P&L',
      value: formatMetric(results.total_pnl, 'currency'),
      icon: DollarSign,
      trend: results.total_pnl > 0 ? 'up' : 'down',
      color: results.total_pnl > 0 ? 'text-green-500' : 'text-red-500',
    },
    {
      title: 'Win Rate',
      value: formatMetric(results.win_rate, 'percent'),
      icon: TrendingUp,
      subtitle: `${results.winning_trades}W / ${results.losing_trades}L`,
    },
    {
      title: 'Sharpe Ratio',
      value: formatMetric(results.sharpe, 'ratio'),
      icon: Activity,
      color: results.sharpe >= 1.5 ? 'text-green-500' : results.sharpe >= 1 ? 'text-yellow-500' : 'text-red-500',
    },
    {
      title: 'Max Drawdown',
      value: formatMetric(results.max_dd, 'percent'),
      icon: TrendingDown,
      color: 'text-red-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header with Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{run.strategy_name}</CardTitle>
              <CardDescription>
                {run.symbol} • {run.timeframe} • {format(new Date(run.start_date), 'MMM d, yyyy')} - {format(new Date(run.end_date), 'MMM d, yyyy')}
              </CardDescription>
            </div>
            <Badge variant={results.total_pnl > 0 ? 'default' : 'destructive'}>
              {results.total_pnl > 0 ? 'Profitable' : 'Loss'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Metric Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            {metricCards.map((metric, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <metric.icon className="h-4 w-4" />
                  {metric.title}
                </div>
                <div className={cn('text-2xl font-bold', metric.color)}>
                  {metric.value}
                </div>
                {metric.subtitle && (
                  <div className="text-xs text-muted-foreground">{metric.subtitle}</div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Results Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="equity">Equity Curve</TabsTrigger>
          <TabsTrigger value="trades">Trade List</TabsTrigger>
          <TabsTrigger value="metrics">All Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Performance Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Profit Factor</div>
                  <div className="text-xl font-semibold">{results.profit_factor.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Total Trades</div>
                  <div className="text-xl font-semibold">{results.total_trades}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Avg Win</div>
                  <div className="text-xl font-semibold text-green-500">
                    {formatMetric(results.avg_win, 'currency')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Avg Loss</div>
                  <div className="text-xl font-semibold text-red-500">
                    {formatMetric(results.avg_loss, 'currency')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Best Trade</div>
                  <div className="text-xl font-semibold text-green-500">
                    {formatMetric(results.best_trade, 'currency')}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Worst Trade</div>
                  <div className="text-xl font-semibold text-red-500">
                    {formatMetric(results.worst_trade, 'currency')}
                  </div>
                </div>
              </div>

              {/* Win/Loss Distribution */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Win Rate Distribution</span>
                  <span>{formatMetric(results.win_rate, 'percent')}</span>
                </div>
                <Progress value={results.win_rate * 100} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="equity">
          <Card>
            <CardHeader>
              <CardTitle>Equity Curve</CardTitle>
              <CardDescription>
                Account balance over time with drawdown visualization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={results.equity_curve}>
                    <defs>
                      <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'MM/dd')}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip
                      labelFormatter={(value) => format(new Date(value as string), 'PPp')}
                      formatter={(value: number, name: string) => {
                        if (name === 'Balance') {
                          return formatMetric(value, 'currency');
                        }
                        return formatMetric(value / 100, 'percent');
                      }}
                    />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="balance"
                      stroke="#10b981"
                      fillOpacity={1}
                      fill="url(#colorBalance)"
                      name="Balance"
                    />
                    <Area
                      yAxisId="right"
                      type="monotone"
                      dataKey="drawdown"
                      stroke="#ef4444"
                      fillOpacity={1}
                      fill="url(#colorDrawdown)"
                      name="Drawdown"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trades">
          <Card>
            <CardHeader>
              <CardTitle>Trade List</CardTitle>
              <CardDescription>
                Detailed list of all executed trades
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead>Entry</TableHead>
                      <TableHead>Exit</TableHead>
                      <TableHead>Qty</TableHead>
                      <TableHead className="text-right">P&L</TableHead>
                      <TableHead className="text-right">%</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.trades.map((trade) => (
                      <TableRow key={trade.id}>
                        <TableCell className="font-mono text-xs">
                          {trade.id}
                        </TableCell>
                        <TableCell>
                          <Badge variant={trade.side === 'long' ? 'default' : 'secondary'}>
                            {trade.side.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <div className="text-sm">${trade.entry_price.toFixed(2)}</div>
                            <div className="text-xs text-muted-foreground">
                              {format(new Date(trade.entry_time), 'MM/dd HH:mm')}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <div className="text-sm">${trade.exit_price.toFixed(2)}</div>
                            <div className="text-xs text-muted-foreground">
                              {format(new Date(trade.exit_time), 'MM/dd HH:mm')}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{trade.quantity}</TableCell>
                        <TableCell className={cn(
                          'text-right font-medium',
                          trade.pnl > 0 ? 'text-green-500' : 'text-red-500'
                        )}>
                          {formatMetric(trade.pnl, 'currency')}
                        </TableCell>
                        <TableCell className={cn(
                          'text-right',
                          trade.pnl_percent > 0 ? 'text-green-500' : 'text-red-500'
                        )}>
                          {formatMetric(trade.pnl_percent / 100, 'percent')}
                        </TableCell>
                        <TableCell>
                          {trade.pnl > 0 ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>All Metrics</CardTitle>
              <CardDescription>
                Comprehensive list of all performance metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries({
                  'Total P&L': formatMetric(results.total_pnl, 'currency'),
                  'Win Rate': formatMetric(results.win_rate, 'percent'),
                  'Sharpe Ratio': formatMetric(results.sharpe, 'ratio'),
                  'Profit Factor': formatMetric(results.profit_factor, 'ratio'),
                  'Max Drawdown': formatMetric(results.max_dd, 'percent'),
                  'Total Trades': results.total_trades,
                  'Winning Trades': results.winning_trades,
                  'Losing Trades': results.losing_trades,
                  'Average Win': formatMetric(results.avg_win, 'currency'),
                  'Average Loss': formatMetric(results.avg_loss, 'currency'),
                  'Best Trade': formatMetric(results.best_trade, 'currency'),
                  'Worst Trade': formatMetric(results.worst_trade, 'currency'),
                  'Max Consecutive Wins': results.max_consecutive_wins,
                  'Max Consecutive Losses': results.max_consecutive_losses,
                  'Duration': run.duration_seconds ? `${run.duration_seconds}s` : 'N/A',
                }).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <div className="text-sm text-muted-foreground">{key}</div>
                    <div className="font-medium">{value}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};