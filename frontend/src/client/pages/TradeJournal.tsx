/**
 * Trade Journal Page
 * Shows historical trades with filters, P&L analysis, and trade details
 */

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { TrendingUp, TrendingDown, DollarSign, Target } from 'lucide-react';
import { cn } from '@/lib/utils';

// Types
interface Trade {
  id: string;
  bot_id: string;
  bot_name: string;
  strategy_id: string;
  strategy_name: string;
  symbol: string;
  direction: 'long' | 'short';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl_usd: number;
  pnl_ticks: number;
  entry_time: string;
  exit_time: string;
  duration_seconds: number;
  commission: number;
  notes: string;
  tags: string[];
}

interface TradesResponse {
  trades: Trade[];
}

// API Functions
const fetchTrades = async (filters: {
  bot_id?: string;
  strategy_id?: string;
  direction?: string;
  winners_only?: boolean;
  losers_only?: boolean;
}): Promise<TradesResponse> => {
  const params = new URLSearchParams();

  if (filters.bot_id) params.append('bot_id', filters.bot_id);
  if (filters.strategy_id) params.append('strategy_id', filters.strategy_id);
  if (filters.direction) params.append('direction', filters.direction);
  if (filters.winners_only) params.append('winners_only', 'true');
  if (filters.losers_only) params.append('losers_only', 'true');

  const response = await fetch(`/api/v1/trades?${params}`);
  if (!response.ok) throw new Error('Failed to fetch trades');
  return response.json();
};

const fetchTradeDetails = async (tradeId: string): Promise<Trade> => {
  const response = await fetch(`/api/v1/trades/${tradeId}`);
  if (!response.ok) throw new Error('Failed to fetch trade details');
  return response.json();
};

const updateTrade = async (
  tradeId: string,
  data: { notes?: string; tags?: string[] }
): Promise<Trade> => {
  const response = await fetch(`/api/v1/trades/${tradeId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update trade');
  return response.json();
};

// Helper Components
const DirectionBadge = ({ direction }: { direction: string }) => (
  <Badge
    variant={direction === 'long' ? 'default' : 'secondary'}
    className={cn(
      'uppercase',
      direction === 'long' && 'bg-green-600 hover:bg-green-700',
      direction === 'short' && 'bg-red-600 hover:bg-red-700'
    )}
  >
    {direction}
  </Badge>
);

const PnLCell = ({ pnl, ticks }: { pnl: number; ticks: number }) => (
  <div
    className={cn(
      'font-mono font-semibold',
      pnl > 0 ? 'text-green-600' : 'text-red-600'
    )}
  >
    <div>${pnl.toFixed(2)}</div>
    <div className="text-xs text-muted-foreground">
      {ticks > 0 ? '+' : ''}
      {ticks.toFixed(2)} ticks
    </div>
  </div>
);

const DurationCell = ({ seconds }: { seconds: number }) => {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return <span className="text-sm text-muted-foreground">{minutes}m {secs}s</span>;
};

// Summary Cards
const SummaryCards = ({ trades }: { trades: Trade[] }) => {
  const summary = useMemo(() => {
    const winners = trades.filter((t) => t.pnl_usd > 0);
    const losers = trades.filter((t) => t.pnl_usd < 0);

    const totalPnl = trades.reduce((sum, t) => sum + t.pnl_usd, 0);
    const totalPnlTicks = trades.reduce((sum, t) => sum + t.pnl_ticks, 0);
    const winRate = winners.length / trades.length;
    const grossWins = winners.reduce((sum, t) => sum + t.pnl_usd, 0);
    const grossLosses = Math.abs(losers.reduce((sum, t) => sum + t.pnl_usd, 0));
    const profitFactor = grossLosses > 0 ? grossWins / grossLosses : 0;

    return {
      totalPnl,
      totalPnlTicks,
      totalTrades: trades.length,
      winners: winners.length,
      losers: losers.length,
      winRate,
      profitFactor,
    };
  }, [trades]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div
            className={cn(
              'text-2xl font-bold',
              summary.totalPnl > 0 ? 'text-green-600' : 'text-red-600'
            )}
          >
            ${summary.totalPnl.toFixed(2)}
          </div>
          <p className="text-xs text-muted-foreground">
            {summary.totalPnlTicks.toFixed(2)} ticks
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(summary.winRate * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">
            {summary.winners}W / {summary.losers}L
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Profit Factor</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {summary.profitFactor.toFixed(2)}
          </div>
          <p className="text-xs text-muted-foreground">Wins/Losses ratio</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
          <TrendingDown className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.totalTrades}</div>
          <p className="text-xs text-muted-foreground">In selected period</p>
        </CardContent>
      </Card>
    </div>
  );
};

// Trade Detail Sheet
const TradeDetailSheet = ({
  tradeId,
  open,
  onClose,
}: {
  tradeId: string | null;
  open: boolean;
  onClose: () => void;
}) => {
  const queryClient = useQueryClient();
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  const { data: trade } = useQuery({
    queryKey: ['trade', tradeId],
    queryFn: () => fetchTradeDetails(tradeId!),
    enabled: !!tradeId && open,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { notes?: string; tags?: string[] }) =>
      updateTrade(tradeId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trade', tradeId] });
      queryClient.invalidateQueries({ queryKey: ['trades'] });
      setEditingNotes(false);
    },
  });

  const handleSaveNotes = () => {
    updateMutation.mutate({ notes });
  };

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      const updatedTags = [...tags, newTag.trim()];
      setTags(updatedTags);
      updateMutation.mutate({ tags: updatedTags });
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const updatedTags = tags.filter((t) => t !== tagToRemove);
    setTags(updatedTags);
    updateMutation.mutate({ tags: updatedTags });
  };

  // Initialize local state when trade data loads
  if (trade && notes === '' && tags.length === 0) {
    setNotes(trade.notes || '');
    setTags(trade.tags || []);
  }

  if (!trade) return null;

  const slippage =
    trade.direction === 'long'
      ? trade.average_fill_price - trade.entry_price
      : trade.entry_price - trade.average_fill_price;

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-[500px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Trade Details</SheetTitle>
          <SheetDescription>
            {trade.symbol} {trade.direction.toUpperCase()} • {trade.bot_name}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Entry/Exit Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-xs text-muted-foreground">Entry Price</Label>
              <div className="font-mono text-lg">${trade.entry_price.toFixed(2)}</div>
              <div className="text-xs text-muted-foreground">
                {new Date(trade.entry_time).toLocaleString()}
              </div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Exit Price</Label>
              <div className="font-mono text-lg">${trade.exit_price.toFixed(2)}</div>
              <div className="text-xs text-muted-foreground">
                {new Date(trade.exit_time).toLocaleString()}
              </div>
            </div>
          </div>

          {/* P&L */}
          <div>
            <Label className="text-xs text-muted-foreground">P&L</Label>
            <div
              className={cn(
                'text-2xl font-bold',
                trade.pnl_usd > 0 ? 'text-green-600' : 'text-red-600'
              )}
            >
              ${trade.pnl_usd.toFixed(2)}
            </div>
            <div className="text-sm text-muted-foreground">
              {trade.pnl_ticks.toFixed(2)} ticks (NQ tick value = $5)
            </div>
          </div>

          {/* Additional Details */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <Label className="text-xs text-muted-foreground">Quantity</Label>
              <div>{trade.quantity} contracts</div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Duration</Label>
              <DurationCell seconds={trade.duration_seconds} />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Commission</Label>
              <div>${trade.commission.toFixed(2)}</div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Strategy</Label>
              <div>{trade.strategy_name}</div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <Label>Trade Notes</Label>
            {editingNotes ? (
              <div className="space-y-2">
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about this trade..."
                  rows={4}
                />
                <div className="flex gap-2">
                  <Button onClick={handleSaveNotes} size="sm">
                    Save
                  </Button>
                  <Button
                    onClick={() => {
                      setEditingNotes(false);
                      setNotes(trade.notes || '');
                    }}
                    variant="outline"
                    size="sm"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div>
                <div className="mt-1 p-3 border rounded-md text-sm min-h-[80px]">
                  {trade.notes || (
                    <span className="text-muted-foreground italic">
                      No notes added
                    </span>
                  )}
                </div>
                <Button
                  onClick={() => setEditingNotes(true)}
                  variant="outline"
                  size="sm"
                  className="mt-2"
                >
                  Edit Notes
                </Button>
              </div>
            )}
          </div>

          {/* Tags */}
          <div>
            <Label>Tags</Label>
            <div className="mt-2 flex flex-wrap gap-2">
              {tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  {tag}
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-2 hover:text-destructive"
                  >
                    ×
                  </button>
                </Badge>
              ))}
            </div>
            <div className="mt-2 flex gap-2">
              <Input
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                placeholder="Add tag..."
                className="flex-1"
              />
              <Button onClick={handleAddTag} size="sm">
                Add
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

// Main Component
export default function TradeJournal() {
  const [filters, setFilters] = useState<{
    direction?: string;
    winners_only?: boolean;
    losers_only?: boolean;
  }>({});
  const [selectedTradeId, setSelectedTradeId] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['trades', filters],
    queryFn: () => fetchTrades(filters),
  });

  const trades = data?.trades || [];

  const handleTradeClick = (tradeId: string) => {
    setSelectedTradeId(tradeId);
    setSheetOpen(true);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Trade Journal</h1>
        <p className="text-muted-foreground">
          Review your trading history and analyze performance
        </p>
      </div>

      {/* Summary Cards */}
      <SummaryCards trades={trades} />

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="w-[200px]">
              <Label>Direction</Label>
              <Select
                value={filters.direction || 'all'}
                onValueChange={(value) =>
                  setFilters((prev) => ({
                    ...prev,
                    direction: value === 'all' ? undefined : value,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="long">Long</SelectItem>
                  <SelectItem value="short">Short</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="w-[200px]">
              <Label>Result</Label>
              <Select
                value={
                  filters.winners_only
                    ? 'winners'
                    : filters.losers_only
                    ? 'losers'
                    : 'all'
                }
                onValueChange={(value) => {
                  if (value === 'winners') {
                    setFilters((prev) => ({
                      ...prev,
                      winners_only: true,
                      losers_only: false,
                    }));
                  } else if (value === 'losers') {
                    setFilters((prev) => ({
                      ...prev,
                      winners_only: false,
                      losers_only: true,
                    }));
                  } else {
                    setFilters((prev) => ({
                      ...prev,
                      winners_only: false,
                      losers_only: false,
                    }));
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="winners">Winners Only</SelectItem>
                  <SelectItem value="losers">Losers Only</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={() => setFilters({})}
                variant="outline"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trades Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {trades.length} trade{trades.length !== 1 ? 's' : ''} found
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading trades...
            </div>
          ) : trades.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No trades found. Adjust your filters or start trading!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Direction</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Entry</TableHead>
                    <TableHead>Exit</TableHead>
                    <TableHead>P&L</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Strategy</TableHead>
                    <TableHead>Bot</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trades.map((trade) => (
                    <TableRow
                      key={trade.id}
                      onClick={() => handleTradeClick(trade.id)}
                      className="cursor-pointer hover:bg-muted/50"
                    >
                      <TableCell>
                        {new Date(trade.exit_time).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <DirectionBadge direction={trade.direction} />
                      </TableCell>
                      <TableCell className="font-mono">{trade.symbol}</TableCell>
                      <TableCell className="font-mono">
                        ${trade.entry_price.toFixed(2)}
                      </TableCell>
                      <TableCell className="font-mono">
                        ${trade.exit_price.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <PnLCell pnl={trade.pnl_usd} ticks={trade.pnl_ticks} />
                      </TableCell>
                      <TableCell>
                        <DurationCell seconds={trade.duration_seconds} />
                      </TableCell>
                      <TableCell className="text-sm">
                        {trade.strategy_name}
                      </TableCell>
                      <TableCell className="text-sm">{trade.bot_name}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trade Detail Sheet */}
      <TradeDetailSheet
        tradeId={selectedTradeId}
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
      />
    </div>
  );
}
