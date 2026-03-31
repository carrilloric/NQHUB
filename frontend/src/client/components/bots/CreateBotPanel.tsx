/**
 * CreateBotPanel Component (AUT-354)
 *
 * Form panel for creating new trading bots.
 * Includes strategy selector, apex account selector, and mode selection.
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus } from 'lucide-react';

interface CreateBotPanelProps {
  strategies: Array<{ id: string; name: string }>;
  apexAccounts: Array<{ id: string; name: string }>;
  onCreate: (data: {
    name: string;
    strategy_id: string;
    mode: 'live' | 'paper';
    apex_account_id?: string;
  }) => void;
  isLoading?: boolean;
}

export function CreateBotPanel({
  strategies,
  apexAccounts,
  onCreate,
  isLoading = false,
}: CreateBotPanelProps) {
  const [name, setName] = useState('');
  const [strategyId, setStrategyId] = useState('');
  const [mode, setMode] = useState<'live' | 'paper'>('paper');
  const [apexAccountId, setApexAccountId] = useState<string | undefined>(undefined);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !strategyId) {
      return;
    }

    onCreate({
      name: name.trim(),
      strategy_id: strategyId,
      mode,
      apex_account_id: mode === 'live' ? apexAccountId : undefined,
    });

    // Reset form
    setName('');
    setStrategyId('');
    setMode('paper');
    setApexAccountId(undefined);
  };

  const isFormValid = name.trim() && strategyId && (mode === 'paper' || apexAccountId);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Create New Bot
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Bot Name */}
          <div className="space-y-2">
            <Label htmlFor="bot-name">
              Bot Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="bot-name"
              placeholder="e.g., Scalping Bot 1"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {/* Strategy Selector */}
          <div className="space-y-2">
            <Label htmlFor="strategy">
              Strategy <span className="text-red-500">*</span>
            </Label>
            <Select
              value={strategyId}
              onValueChange={setStrategyId}
              disabled={isLoading}
            >
              <SelectTrigger id="strategy">
                <SelectValue placeholder="Select a strategy" />
              </SelectTrigger>
              <SelectContent>
                {strategies.map((strategy) => (
                  <SelectItem key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Mode Selector */}
          <div className="space-y-2">
            <Label htmlFor="mode">
              Mode <span className="text-red-500">*</span>
            </Label>
            <Select
              value={mode}
              onValueChange={(value) => setMode(value as 'live' | 'paper')}
              disabled={isLoading}
            >
              <SelectTrigger id="mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="paper">📝 Paper Trading</SelectItem>
                <SelectItem value="live">🔴 Live Trading</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Apex Account Selector (only for live mode) */}
          {mode === 'live' && (
            <div className="space-y-2">
              <Label htmlFor="apex-account">
                Apex Account <span className="text-red-500">*</span>
              </Label>
              <Select
                value={apexAccountId}
                onValueChange={setApexAccountId}
                disabled={isLoading}
              >
                <SelectTrigger id="apex-account">
                  <SelectValue placeholder="Select an Apex account" />
                </SelectTrigger>
                <SelectContent>
                  {apexAccounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Required for live trading mode
              </p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={!isFormValid || isLoading}
          >
            {isLoading ? 'Creating...' : 'Create Bot'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
