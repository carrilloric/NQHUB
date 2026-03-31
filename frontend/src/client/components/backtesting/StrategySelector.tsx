import React, { useEffect, useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useBacktest } from '@/hooks/useBacktest';

interface Strategy {
  id: string;
  name: string;
  description: string;
}

interface StrategySelectorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function StrategySelector({ value, onChange, disabled }: StrategySelectorProps) {
  const { getStrategies } = useBacktest();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStrategies = async () => {
      setLoading(true);
      try {
        const data = await getStrategies();
        setStrategies(data);
        // Auto-select first strategy if none selected
        if (!value && data.length > 0) {
          onChange(data[0].id);
        }
      } catch (error) {
        console.error('Failed to load strategies:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStrategies();
  }, [getStrategies]);

  return (
    <div className="space-y-2">
      <Label htmlFor="strategy-selector">Strategy</Label>
      <Select
        value={value}
        onValueChange={onChange}
        disabled={disabled || loading}
      >
        <SelectTrigger
          id="strategy-selector"
          className="w-full"
          data-testid="strategy-selector"
        >
          <SelectValue placeholder={loading ? 'Loading strategies...' : 'Select a strategy'} />
        </SelectTrigger>
        <SelectContent>
          {strategies.map((strategy) => (
            <SelectItem
              key={strategy.id}
              value={strategy.id}
              className="cursor-pointer"
            >
              <div className="flex flex-col">
                <span className="font-medium">{strategy.name}</span>
                <span className="text-sm text-muted-foreground">
                  {strategy.description}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}