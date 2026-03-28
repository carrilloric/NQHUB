/**
 * Run Configuration Form Component
 * Form for configuring backtest parameters
 */

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
import { Separator } from '@/components/ui/separator';
import { StrategySelector } from './StrategySelector';
import { PlayCircle, Settings, Calendar as CalendarIcon, Info } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface RunConfig {
  strategy_id?: string;
  start_date?: Date;
  end_date?: Date;
  symbol: string;
  timeframe: string;
  parameters: Record<string, any>;
}

interface RunConfigFormProps {
  onRun: (config: RunConfig) => Promise<void>;
  isRunning?: boolean;
}

export const RunConfigForm: React.FC<RunConfigFormProps> = ({
  onRun,
  isRunning = false,
}) => {
  const [config, setConfig] = useState<RunConfig>({
    symbol: 'NQ',
    timeframe: '1h',
    parameters: {},
  });
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null);
  const [customParams, setCustomParams] = useState<Record<string, string>>({});

  const handleStrategySelect = (strategyId: string, strategy: any) => {
    setConfig({ ...config, strategy_id: strategyId });
    setSelectedStrategy(strategy);

    // Initialize custom parameters from strategy config
    if (strategy.config) {
      const params: Record<string, string> = {};
      Object.entries(strategy.config).forEach(([key, value]) => {
        params[key] = String(value);
      });
      setCustomParams(params);
    }
  };

  const handleParamChange = (key: string, value: string) => {
    setCustomParams({ ...customParams, [key]: value });
    setConfig({
      ...config,
      parameters: { ...config.parameters, [key]: parseParamValue(value) },
    });
  };

  const parseParamValue = (value: string): any => {
    // Try to parse as number
    const num = Number(value);
    if (!isNaN(num)) return num;

    // Try to parse as boolean
    if (value === 'true') return true;
    if (value === 'false') return false;

    // Return as string
    return value;
  };

  const handleSubmit = async () => {
    // Validation
    if (!config.strategy_id) {
      toast.error('Please select a strategy');
      return;
    }

    if (!config.start_date) {
      toast.error('Please select a start date');
      return;
    }

    if (!config.end_date) {
      toast.error('Please select an end date');
      return;
    }

    if (config.start_date >= config.end_date) {
      toast.error('End date must be after start date');
      return;
    }

    // Convert custom params to config parameters
    const parameters: Record<string, any> = {};
    Object.entries(customParams).forEach(([key, value]) => {
      parameters[key] = parseParamValue(value);
    });

    await onRun({
      ...config,
      parameters,
    });
  };

  const commonTimeframes = [
    { value: '1m', label: '1 Minute' },
    { value: '5m', label: '5 Minutes' },
    { value: '15m', label: '15 Minutes' },
    { value: '30m', label: '30 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Backtest Configuration
        </CardTitle>
        <CardDescription>
          Configure your strategy and backtest parameters
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Strategy Selection */}
        <div className="space-y-2">
          <Label>Strategy</Label>
          <StrategySelector
            value={config.strategy_id}
            onSelect={handleStrategySelect}
          />
        </div>

        <Separator />

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
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {config.start_date ? (
                    format(config.start_date, 'PPP')
                  ) : (
                    <span>Pick a date</span>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={config.start_date}
                  onSelect={(date) => setConfig({ ...config, start_date: date })}
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
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {config.end_date ? (
                    format(config.end_date, 'PPP')
                  ) : (
                    <span>Pick a date</span>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={config.end_date}
                  onSelect={(date) => setConfig({ ...config, end_date: date })}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* Symbol and Timeframe */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Symbol</Label>
            <Select
              value={config.symbol}
              onValueChange={(symbol) => setConfig({ ...config, symbol })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NQ">NQ (Nasdaq-100 E-mini)</SelectItem>
                <SelectItem value="ES">ES (S&P 500 E-mini)</SelectItem>
                <SelectItem value="YM">YM (Dow E-mini)</SelectItem>
                <SelectItem value="RTY">RTY (Russell 2000 E-mini)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Timeframe</Label>
            <Select
              value={config.timeframe}
              onValueChange={(timeframe) => setConfig({ ...config, timeframe })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {commonTimeframes.map((tf) => (
                  <SelectItem key={tf.value} value={tf.value}>
                    {tf.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <Separator />

        {/* Strategy Parameters */}
        {selectedStrategy && selectedStrategy.config && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Label>Strategy Parameters</Label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Customize strategy-specific parameters</p>
                </TooltipContent>
              </Tooltip>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(selectedStrategy.config).map(([key, defaultValue]) => (
                <div key={key} className="space-y-2">
                  <Label htmlFor={key} className="text-sm capitalize">
                    {key.replace(/_/g, ' ')}
                  </Label>
                  <Input
                    id={key}
                    type="text"
                    value={customParams[key] || String(defaultValue)}
                    onChange={(e) => handleParamChange(key, e.target.value)}
                    placeholder={String(defaultValue)}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Run Button */}
        <Button
          onClick={handleSubmit}
          disabled={isRunning || !config.strategy_id}
          className="w-full"
          size="lg"
        >
          {isRunning ? (
            <>
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              Running Backtest...
            </>
          ) : (
            <>
              <PlayCircle className="mr-2 h-4 w-4" />
              Run Backtest
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};