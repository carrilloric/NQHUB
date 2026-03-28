/**
 * Strategy Selector Component
 * Allows selection of existing strategies or creation of new ones
 */

import React, { useEffect, useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Plus, Code, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

interface Strategy {
  id: string;
  name: string;
  type: string;
  version: string;
  status: string;
  description: string;
  tags: string[];
  metrics?: {
    total_runs: number;
    avg_sharpe: number;
    avg_win_rate: number;
    best_profit_factor: number;
  };
}

interface StrategySelectorProps {
  value?: string;
  onSelect: (strategyId: string, strategy: Strategy) => void;
  className?: string;
}

export const StrategySelector: React.FC<StrategySelectorProps> = ({
  value,
  onSelect,
  className,
}) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newStrategy, setNewStrategy] = useState({
    name: '',
    type: 'trend_following',
    description: '',
    tags: '',
  });

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await fetch('/api/v1/backtest/strategies');
      if (!response.ok) throw new Error('Failed to fetch strategies');
      const data = await response.json();
      setStrategies(data.strategies || []);
    } catch (error) {
      toast.error('Failed to load strategies');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStrategy = async () => {
    try {
      const response = await fetch('/api/v1/backtest/strategies/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newStrategy,
          tags: newStrategy.tags.split(',').map(t => t.trim()).filter(Boolean),
        }),
      });

      if (!response.ok) throw new Error('Failed to create strategy');

      const created = await response.json();
      setStrategies([...strategies, created]);
      onSelect(created.id, created);
      setIsCreateOpen(false);
      toast.success('Strategy created successfully');

      // Reset form
      setNewStrategy({
        name: '',
        type: 'trend_following',
        description: '',
        tags: '',
      });
    } catch (error) {
      toast.error('Failed to create strategy');
      console.error(error);
    }
  };

  const selectedStrategy = strategies.find(s => s.id === value);

  return (
    <div className={className}>
      <div className="flex items-center gap-2">
        <Select value={value} onValueChange={(id) => {
          const strategy = strategies.find(s => s.id === id);
          if (strategy) onSelect(id, strategy);
        }}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a strategy">
              {selectedStrategy && (
                <div className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  <span>{selectedStrategy.name}</span>
                  <Badge variant="secondary" className="ml-auto">
                    v{selectedStrategy.version}
                  </Badge>
                </div>
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {loading ? (
              <div className="p-2 text-center text-muted-foreground">
                Loading strategies...
              </div>
            ) : strategies.length === 0 ? (
              <div className="p-2 text-center text-muted-foreground">
                No strategies available
              </div>
            ) : (
              strategies.map((strategy) => (
                <SelectItem key={strategy.id} value={strategy.id}>
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-2">
                      <span>{strategy.name}</span>
                      <Badge variant="outline">{strategy.type}</Badge>
                    </div>
                    {strategy.metrics && strategy.metrics.total_runs > 0 && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <TrendingUp className="h-3 w-3" />
                        <span>
                          Sharpe: {strategy.metrics.avg_sharpe.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </SelectItem>
              ))
            )}
          </SelectContent>
        </Select>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button size="icon" variant="outline">
              <Plus className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Strategy</DialogTitle>
              <DialogDescription>
                Define a new trading strategy for backtesting
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Strategy Name</Label>
                <Input
                  id="name"
                  value={newStrategy.name}
                  onChange={(e) => setNewStrategy({ ...newStrategy, name: e.target.value })}
                  placeholder="e.g., Moving Average Crossover"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select
                  value={newStrategy.type}
                  onValueChange={(type) => setNewStrategy({ ...newStrategy, type })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="trend_following">Trend Following</SelectItem>
                    <SelectItem value="mean_reversion">Mean Reversion</SelectItem>
                    <SelectItem value="momentum">Momentum</SelectItem>
                    <SelectItem value="arbitrage">Arbitrage</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newStrategy.description}
                  onChange={(e) => setNewStrategy({ ...newStrategy, description: e.target.value })}
                  placeholder="Describe your strategy..."
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tags">Tags (comma-separated)</Label>
                <Input
                  id="tags"
                  value={newStrategy.tags}
                  onChange={(e) => setNewStrategy({ ...newStrategy, tags: e.target.value })}
                  placeholder="e.g., MA, trend, stocks"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateStrategy} disabled={!newStrategy.name}>
                Create Strategy
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {selectedStrategy && selectedStrategy.description && (
        <p className="mt-2 text-sm text-muted-foreground">
          {selectedStrategy.description}
        </p>
      )}
    </div>
  );
};