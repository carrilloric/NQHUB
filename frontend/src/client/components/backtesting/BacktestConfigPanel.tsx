import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { CalendarIcon, PlayIcon, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { StrategySelector } from './StrategySelector';
import { useBacktest, BacktestConfig } from '@/hooks/useBacktest';
import { toast } from 'sonner';

interface BacktestConfigPanelProps {
  onRunComplete?: (backtestId: string) => void;
}

export function BacktestConfigPanel({ onRunComplete }: BacktestConfigPanelProps) {
  const { runBacktest, isRunning, progress } = useBacktest();

  const [config, setConfig] = useState<BacktestConfig>({
    strategy_id: '',
    start_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    initial_capital: 25000,
    timeframe: '1h',
    commission_per_side: 2.25,
    slippage_ticks: 1,
    symbol: 'NQ',
  });

  const handleRun = async () => {
    if (!config.strategy_id) {
      toast.error('Please select a strategy');
      return;
    }

    const taskId = await runBacktest(config);
    if (taskId && onRunComplete) {
      // Will be called when backtest completes
      onRunComplete(taskId);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Backtest Configuration</CardTitle>
        <CardDescription>
          Configure and run your backtest
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Strategy Selection */}
        <StrategySelector
          value={config.strategy_id}
          onChange={(value) => setConfig({ ...config, strategy_id: value })}
          disabled={isRunning}
        />

        {/* Timeframe */}
        <div className="space-y-2">
          <Label htmlFor="timeframe">Timeframe</Label>
          <Select
            value={config.timeframe}
            onValueChange={(value: '1min' | '5min' | '15min' | '1h') =>
              setConfig({ ...config, timeframe: value })
            }
            disabled={isRunning}
          >
            <SelectTrigger id="timeframe">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1min">1 Minute</SelectItem>
              <SelectItem value="5min">5 Minutes</SelectItem>
              <SelectItem value="15min">15 Minutes</SelectItem>
              <SelectItem value="1h">1 Hour</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Start Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    'w-full justify-start text-left font-normal',
                    !config.start_date && 'text-muted-foreground'
                  )}
                  disabled={isRunning}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {config.start_date
                    ? format(new Date(config.start_date), 'PPP')
                    : <span>Pick a date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={config.start_date ? new Date(config.start_date) : undefined}
                  onSelect={(date) =>
                    setConfig({ ...config, start_date: date ? format(date, 'yyyy-MM-dd') : '' })
                  }
                  disabled={(date) =>
                    date > new Date() || date < new Date('2020-01-01')
                  }
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          <div className="space-y-2">
            <Label>End Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    'w-full justify-start text-left font-normal',
                    !config.end_date && 'text-muted-foreground'
                  )}
                  disabled={isRunning}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {config.end_date
                    ? format(new Date(config.end_date), 'PPP')
                    : <span>Pick a date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={config.end_date ? new Date(config.end_date) : undefined}
                  onSelect={(date) =>
                    setConfig({ ...config, end_date: date ? format(date, 'yyyy-MM-dd') : '' })
                  }
                  disabled={(date) =>
                    date > new Date() || date < new Date('2020-01-01')
                  }
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* Capital Configuration */}
        <div className="space-y-2">
          <Label htmlFor="initial-capital">Initial Capital ($)</Label>
          <Input
            id="initial-capital"
            type="number"
            value={config.initial_capital}
            onChange={(e) =>
              setConfig({ ...config, initial_capital: Number(e.target.value) })
            }
            disabled={isRunning}
            min={1000}
            step={1000}
          />
        </div>

        {/* Slippage & Commission */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="commission">Commission ($/side)</Label>
            <Input
              id="commission"
              type="number"
              value={config.commission_per_side}
              onChange={(e) =>
                setConfig({ ...config, commission_per_side: Number(e.target.value) })
              }
              disabled={isRunning}
              min={0}
              step={0.25}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="slippage">Slippage (ticks)</Label>
            <Input
              id="slippage"
              type="number"
              value={config.slippage_ticks}
              onChange={(e) =>
                setConfig({ ...config, slippage_ticks: Number(e.target.value) })
              }
              disabled={isRunning}
              min={0}
              step={1}
            />
          </div>
        </div>

        {/* Run Button */}
        <Button
          onClick={handleRun}
          disabled={isRunning || !config.strategy_id}
          className="w-full"
          data-testid="run-backtest-button"
        >
          {isRunning ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running... {progress}%
            </>
          ) : (
            <>
              <PlayIcon className="mr-2 h-4 w-4" />
              Run Backtest
            </>
          )}
        </Button>

        {/* NQ Hardcoded Info */}
        <div className="mt-4 p-3 bg-muted rounded-lg text-sm">
          <div className="font-semibold mb-1">NQ Contract Specs</div>
          <div className="grid grid-cols-3 gap-2 text-muted-foreground">
            <div>Tick Size: $0.25</div>
            <div>Tick Value: $5</div>
            <div>Point Value: $20</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}