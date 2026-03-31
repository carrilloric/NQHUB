import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BacktestConfigPanel } from '@/components/backtesting/BacktestConfigPanel';
import { ApexComplianceCard } from '@/components/backtesting/ApexComplianceCard';
import { EquityCurveChart } from '@/components/backtesting/EquityCurveChart';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useBacktest } from '@/hooks/useBacktest';
import { Loader2 } from 'lucide-react';

// Simple MetricsTable component inline for now
function MetricsTable({ metrics }: { metrics: any }) {
  if (!metrics) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Metrics</CardTitle>
        <CardDescription>Key statistics from backtest</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Sharpe Ratio</span>
              <span className="font-mono">{metrics.sharpe_ratio.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Sortino Ratio</span>
              <span className="font-mono">{metrics.sortino_ratio.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Win Rate</span>
              <span className="font-mono">{(metrics.win_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Profit Factor</span>
              <span className="font-mono">{metrics.profit_factor.toFixed(2)}</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Max Drawdown</span>
              <span className="font-mono text-red-600">
                {(metrics.max_drawdown * 100).toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Trades</span>
              <span className="font-mono">{metrics.total_trades}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Annual Return</span>
              <span className="font-mono">{(metrics.annual_return * 100).toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Calmar Ratio</span>
              <span className="font-mono">{metrics.calmar_ratio.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Simple TradeListTable component inline
function TradeListTable({ backtestId }: { backtestId: string }) {
  const { getBacktestTrades } = useBacktest();
  const [trades, setTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  React.useEffect(() => {
    const loadTrades = async () => {
      if (!backtestId) return;
      setLoading(true);
      try {
        const result = await getBacktestTrades(backtestId, page, 10);
        setTrades(result.trades);
        setTotal(result.total);
      } catch (error) {
        console.error('Failed to load trades:', error);
      } finally {
        setLoading(false);
      }
    };
    loadTrades();
  }, [backtestId, page, getBacktestTrades]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade List</CardTitle>
        <CardDescription>All executed trades</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">#</th>
                    <th className="text-left p-2">Entry Time</th>
                    <th className="text-left p-2">Side</th>
                    <th className="text-right p-2">Entry</th>
                    <th className="text-right p-2">Exit</th>
                    <th className="text-right p-2">Qty</th>
                    <th className="text-right p-2">Net P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((trade) => (
                    <tr key={trade.trade_id} className="border-b">
                      <td className="p-2">{trade.trade_id}</td>
                      <td className="p-2">{new Date(trade.entry_time).toLocaleString()}</td>
                      <td className="p-2">
                        <span className={trade.side === 'LONG' ? 'text-green-600' : 'text-red-600'}>
                          {trade.side}
                        </span>
                      </td>
                      <td className="p-2 text-right font-mono">{trade.entry_price.toFixed(2)}</td>
                      <td className="p-2 text-right font-mono">{trade.exit_price.toFixed(2)}</td>
                      <td className="p-2 text-right">{trade.quantity}</td>
                      <td className={`p-2 text-right font-mono ${trade.net_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${trade.net_pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {total > 10 && (
              <div className="flex items-center justify-between mt-4">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {Math.ceil(total / 10)}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(total / 10)}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function BacktestingPage() {
  const { results, isRunning } = useBacktest();
  const [activeTab, setActiveTab] = useState('config');

  // When backtest completes, switch to results tab
  React.useEffect(() => {
    if (results && !isRunning) {
      setActiveTab('results');
    }
  }, [results, isRunning]);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Backtesting</h1>
        <p className="text-muted-foreground">
          Run and analyze trading strategy backtests
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="results" disabled={!results}>
            Results
          </TabsTrigger>
          <TabsTrigger value="comparison" disabled={!results}>
            Comparison
          </TabsTrigger>
        </TabsList>

        <TabsContent value="config" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <BacktestConfigPanel />
            </div>
            <div className="lg:col-span-2">
              {results ? (
                <div className="space-y-6">
                  <EquityCurveChart
                    data={results.equity_curve}
                    initialCapital={25000}
                  />
                  <ApexComplianceCard compliance={results.apex_compliance} />
                </div>
              ) : (
                <Card>
                  <CardContent className="flex items-center justify-center h-96">
                    <div className="text-center">
                      <p className="text-muted-foreground">
                        Configure and run a backtest to see results
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="results" className="space-y-6">
          {results && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <MetricsTable metrics={results.metrics} />
                <ApexComplianceCard compliance={results.apex_compliance} />
              </div>
              <EquityCurveChart
                data={results.equity_curve}
                initialCapital={25000}
              />
              <TradeListTable backtestId={results.backtest_id} />
            </>
          )}
        </TabsContent>

        <TabsContent value="comparison">
          <Card>
            <CardContent className="flex items-center justify-center h-96">
              <p className="text-muted-foreground">
                Comparison view coming soon...
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}