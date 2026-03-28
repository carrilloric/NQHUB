/**
 * Rule-Based Backtesting Page
 * Traditional algorithmic strategy testing with comprehensive UI
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  PlayCircle,
  Settings,
  FileText,
  TrendingUp,
  BarChart3,
  GitCompare,
  RefreshCw,
  Download,
  Upload,
} from 'lucide-react';
import {
  RunConfigForm,
  BacktestResults,
  ComparisonView,
} from '@/components/backtesting';
import { toast } from 'sonner';
import { format } from 'date-fns';

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
  config?: Record<string, any>;
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
    trades: Array<any>;
  };
}

const BacktestingRuleBased: React.FC = () => {
  const [activeTab, setActiveTab] = useState('configure');
  const [isRunning, setIsRunning] = useState(false);
  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [currentRun, setCurrentRun] = useState<BacktestRun | undefined>();
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);
  const [comparisonMode, setComparisonMode] = useState(false);

  // Load runs on mount
  useEffect(() => {
    fetchRuns();
  }, []);

  // Poll for pending/running runs
  useEffect(() => {
    const interval = setInterval(() => {
      const hasPending = runs.some(r => r.status === 'pending' || r.status === 'running');
      if (hasPending) {
        fetchRuns();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [runs]);

  const fetchRuns = async () => {
    try {
      const response = await fetch('/api/v1/backtest/runs');
      if (!response.ok) throw new Error('Failed to fetch runs');
      const data = await response.json();
      setRuns(data.runs || []);

      // Update current run if it exists
      if (currentRun) {
        const updated = data.runs.find((r: BacktestRun) => r.id === currentRun.id);
        if (updated) {
          setCurrentRun(updated);
        }
      }
    } catch (error) {
      console.error('Failed to fetch runs:', error);
    }
  };

  const handleRunBacktest = async (config: any) => {
    setIsRunning(true);
    try {
      const response = await fetch('/api/v1/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          start_date: format(config.start_date, 'yyyy-MM-dd'),
          end_date: format(config.end_date, 'yyyy-MM-dd'),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start backtest');
      }

      const newRun = await response.json();
      setRuns([newRun, ...runs]);
      setCurrentRun(newRun);
      setActiveTab('results');
      toast.success('Backtest started successfully');

      // Start polling for completion
      setTimeout(fetchRuns, 1000);
    } catch (error) {
      toast.error('Failed to run backtest');
      console.error(error);
    } finally {
      setIsRunning(false);
    }
  };

  const handleExportResults = () => {
    if (!currentRun || !currentRun.results) {
      toast.error('No results to export');
      return;
    }

    const dataStr = JSON.stringify(currentRun, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

    const exportFileDefaultName = `backtest-${currentRun.strategy_name}-${currentRun.id}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();

    toast.success('Results exported successfully');
  };

  const handleToggleComparison = (runId: string) => {
    if (selectedRuns.includes(runId)) {
      setSelectedRuns(selectedRuns.filter(id => id !== runId));
    } else if (selectedRuns.length < 5) {
      setSelectedRuns([...selectedRuns, runId]);
    } else {
      toast.warning('Maximum 5 runs can be compared');
    }
  };

  // Calculate summary metrics
  const completedRuns = runs.filter(r => r.status === 'completed' && r.results);
  const bestSharpe = Math.max(...completedRuns.map(r => r.results?.sharpe || 0));
  const avgWinRate = completedRuns.length > 0
    ? completedRuns.reduce((acc, r) => acc + (r.results?.win_rate || 0), 0) / completedRuns.length
    : 0;
  const worstDrawdown = Math.min(...completedRuns.map(r => r.results?.max_dd || 0));

  return (
    <div className="flex-1 space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Rule-Based Backtesting</h2>
          <p className="text-muted-foreground">
            Test and optimize your trading strategies with historical data
          </p>
        </div>
        <div className="flex items-center gap-2">
          {activeTab === 'results' && currentRun?.results && (
            <Button variant="outline" onClick={handleExportResults}>
              <Download className="mr-2 h-4 w-4" />
              Export Results
            </Button>
          )}
          {activeTab === 'history' && selectedRuns.length >= 2 && (
            <Button onClick={() => setActiveTab('compare')}>
              <GitCompare className="mr-2 h-4 w-4" />
              Compare Selected ({selectedRuns.length})
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{runs.length}</div>
            <p className="text-xs text-muted-foreground">
              {completedRuns.length} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Best Sharpe</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {bestSharpe > 0 ? bestSharpe.toFixed(2) : '-'}
            </div>
            <p className="text-xs text-muted-foreground">
              Risk-adjusted return
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Win Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {avgWinRate > 0 ? `${(avgWinRate * 100).toFixed(1)}%` : '-'}
            </div>
            <p className="text-xs text-muted-foreground">
              Across all strategies
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {worstDrawdown < 0 ? `${(worstDrawdown * 100).toFixed(1)}%` : '-'}
            </div>
            <p className="text-xs text-muted-foreground">
              Worst recorded drawdown
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="configure">Configure</TabsTrigger>
          <TabsTrigger value="results">
            Results
            {currentRun?.status === 'running' && (
              <RefreshCw className="ml-2 h-3 w-3 animate-spin" />
            )}
          </TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="compare" disabled={selectedRuns.length < 2}>
            Compare
          </TabsTrigger>
        </TabsList>

        <TabsContent value="configure" className="space-y-4">
          <RunConfigForm onRun={handleRunBacktest} isRunning={isRunning} />
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          <BacktestResults run={currentRun} />
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Backtest History</CardTitle>
                  <CardDescription>
                    Previous backtest runs and their results
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchRuns}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {runs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No backtest history available
                </div>
              ) : (
                <div className="space-y-2">
                  {runs.map((run) => (
                    <div
                      key={run.id}
                      className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 cursor-pointer"
                      onClick={() => {
                        setCurrentRun(run);
                        setActiveTab('results');
                      }}
                    >
                      <div className="flex items-center gap-4">
                        {comparisonMode && (
                          <Checkbox
                            checked={selectedRuns.includes(run.id)}
                            onCheckedChange={() => handleToggleComparison(run.id)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        )}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{run.strategy_name}</span>
                            <Badge
                              variant={
                                run.status === 'completed' ? 'default' :
                                run.status === 'running' ? 'secondary' :
                                run.status === 'failed' ? 'destructive' :
                                'outline'
                              }
                            >
                              {run.status}
                            </Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {run.symbol} • {run.timeframe} • {format(new Date(run.created_at), 'MMM d, yyyy HH:mm')}
                          </div>
                        </div>
                      </div>
                      {run.results && (
                        <div className="flex items-center gap-6 text-sm">
                          <div>
                            <span className="text-muted-foreground">P&L: </span>
                            <span className={run.results.total_pnl > 0 ? 'text-green-500' : 'text-red-500'}>
                              ${run.results.total_pnl.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Sharpe: </span>
                            <span>{run.results.sharpe.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Win Rate: </span>
                            <span>{(run.results.win_rate * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compare" className="space-y-4">
          <ComparisonView
            runs={runs.filter(r => selectedRuns.includes(r.id))}
            onRemove={(id) => setSelectedRuns(selectedRuns.filter(sid => sid !== id))}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BacktestingRuleBased;