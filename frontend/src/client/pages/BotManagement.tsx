/**
 * Bot Management Page
 * Allows creating, starting, stopping, and killing bots
 * Shows real-time bot status via WebSocket 'bot' channel
 * Based on CONTRACT-004 Live Trading API
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Bot as BotIcon,
  PlayCircle,
  Square,
  Skull,
  AlertTriangle,
  Activity,
  Clock,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useNQHubWebSocket } from '@/hooks/useNQHubWebSocket';
import { useWebSocketMessages } from '@/state/websocket.store';

// Types from CONTRACT-004
interface Bot {
  id: string;
  name: string;
  strategy_id: string;
  status: 'stopped' | 'running' | 'killed' | 'error';
  mode: 'live' | 'paper' | 'simulation';
  last_heartbeat: string;
  apex_account_id: string | null;
  active_params: Record<string, any>;
}

interface StateLogEntry {
  from: string;
  to: string;
  reason: string;
  timestamp: string;
}

interface CreateBotData {
  name: string;
  strategy_id: string;
  mode: 'live' | 'paper' | 'simulation';
  apex_account_id?: string;
}

const API_BASE = '/api/v1';

// Status badge component
const StatusBadge: React.FC<{ status: Bot['status'] }> = ({ status }) => {
  const variants: Record<Bot['status'], { color: string; label: string }> = {
    stopped: { color: 'bg-gray-500', label: 'Stopped' },
    running: { color: 'bg-green-500', label: 'Running' },
    error: { color: 'bg-red-500', label: 'Error' },
    killed: { color: 'bg-black', label: 'Killed' },
  };

  const variant = variants[status];

  return (
    <Badge className={`${variant.color} text-white`}>
      {variant.label}
    </Badge>
  );
};

// Heartbeat indicator component
const HeartbeatIndicator: React.FC<{ lastHeartbeat: string }> = ({
  lastHeartbeat,
}) => {
  const [color, setColor] = useState('bg-green-500');

  useEffect(() => {
    const updateColor = () => {
      const secondsAgo =
        (Date.now() - new Date(lastHeartbeat).getTime()) / 1000;

      if (secondsAgo < 60) {
        setColor('bg-green-500');
      } else if (secondsAgo < 120) {
        setColor('bg-yellow-500');
      } else {
        setColor('bg-red-500');
      }
    };

    updateColor();
    const interval = setInterval(updateColor, 1000);
    return () => clearInterval(interval);
  }, [lastHeartbeat]);

  const secondsAgo = Math.floor(
    (Date.now() - new Date(lastHeartbeat).getTime()) / 1000
  );

  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${color}`} />
      <span className="text-sm text-muted-foreground">
        {secondsAgo < 60
          ? `${secondsAgo}s ago`
          : secondsAgo < 120
          ? `${Math.floor(secondsAgo / 60)}m ago`
          : `${Math.floor(secondsAgo / 60)}m ago`}
      </span>
    </div>
  );
};

const BotManagement: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // WebSocket connection for real-time bot updates
  const { connected, subscribe, unsubscribe } = useNQHubWebSocket();
  const { lastMessage } = useWebSocketMessages('bot');

  // State for bot selection and dialogs
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null);
  const [killDialogOpen, setKillDialogOpen] = useState(false);
  const [killAllDialogOpen, setKillAllDialogOpen] = useState(false);
  const [botToKill, setBotToKill] = useState<string | null>(null);

  // State for create bot form
  const [createFormOpen, setCreateFormOpen] = useState(false);
  const [createFormData, setCreateFormData] = useState<CreateBotData>({
    name: '',
    strategy_id: '',
    mode: 'paper',
  });

  // Subscribe to bot channel on mount
  useEffect(() => {
    if (connected) {
      subscribe(['bot']);
    }

    return () => {
      if (connected) {
        unsubscribe(['bot']);
      }
    };
  }, [connected, subscribe, unsubscribe]);

  // Handle WebSocket messages for bot updates
  useEffect(() => {
    if (lastMessage) {
      console.log('[BotManagement] Received bot update:', lastMessage);
      // Refetch bots list when we receive a bot update
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    }
  }, [lastMessage, queryClient]);

  // Fetch bots list
  const { data: botsData, isLoading: botsLoading } = useQuery({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/bots`);
      if (!response.ok) throw new Error('Failed to fetch bots');
      return response.json() as Promise<{ bots: Bot[] }>;
    },
  });

  // Fetch state log for selected bot
  const { data: stateLogData } = useQuery({
    queryKey: ['bot-state-log', selectedBot?.id],
    queryFn: async () => {
      if (!selectedBot) return null;
      const response = await fetch(
        `${API_BASE}/bots/${selectedBot.id}/state-log`
      );
      if (!response.ok) throw new Error('Failed to fetch state log');
      return response.json() as Promise<{ states: StateLogEntry[] }>;
    },
    enabled: !!selectedBot,
  });

  // Create bot mutation
  const createBotMutation = useMutation({
    mutationFn: async (data: CreateBotData) => {
      const response = await fetch(`${API_BASE}/bots/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create bot');
      return response.json();
    },
    onSuccess: () => {
      toast({ title: 'Bot created successfully' });
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      setCreateFormOpen(false);
      setCreateFormData({ name: '', strategy_id: '', mode: 'paper' });
    },
    onError: () => {
      toast({ title: 'Failed to create bot', variant: 'destructive' });
    },
  });

  // Start bot mutation
  const startBotMutation = useMutation({
    mutationFn: async (botId: string) => {
      const response = await fetch(`${API_BASE}/bots/${botId}/start`, {
        method: 'POST',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start bot');
      }
      return response.json();
    },
    onSuccess: () => {
      toast({ title: 'Bot started successfully' });
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to start bot',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Stop bot mutation
  const stopBotMutation = useMutation({
    mutationFn: async (botId: string) => {
      const response = await fetch(`${API_BASE}/bots/${botId}/stop`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to stop bot');
      return response.json();
    },
    onSuccess: () => {
      toast({ title: 'Bot stopped successfully' });
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
    onError: () => {
      toast({ title: 'Failed to stop bot', variant: 'destructive' });
    },
  });

  // Kill bot mutation
  const killBotMutation = useMutation({
    mutationFn: async (botId: string) => {
      const response = await fetch(`${API_BASE}/bots/${botId}/kill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'User initiated kill' }),
      });
      if (!response.ok) throw new Error('Failed to kill bot');
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: 'Bot killed',
        description: 'Bot has been terminated',
        variant: 'destructive',
      });
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      setKillDialogOpen(false);
      setBotToKill(null);
    },
    onError: () => {
      toast({ title: 'Failed to kill bot', variant: 'destructive' });
    },
  });

  // Kill all bots mutation
  const killAllBotsMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE}/bots/kill-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          confirm: 'KILL_ALL_BOTS',
          reason: 'Global kill switch activated by user',
        }),
      });
      if (!response.ok) throw new Error('Failed to kill all bots');
      return response.json();
    },
    onSuccess: (data) => {
      toast({
        title: 'All bots killed',
        description: `Killed ${data.killed_count} bots`,
        variant: 'destructive',
      });
      queryClient.invalidateQueries({ queryKey: ['bots'] });
      setKillAllDialogOpen(false);
    },
    onError: () => {
      toast({ title: 'Failed to kill all bots', variant: 'destructive' });
    },
  });

  const bots = botsData?.bots || [];
  const runningBots = bots.filter((bot) => bot.status === 'running');

  return (
    <div className="flex-1 space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Bot Management
          </h2>
          <p className="text-muted-foreground">
            Create, manage, and monitor trading bots
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setCreateFormOpen(!createFormOpen)}
          >
            <BotIcon className="mr-2 h-4 w-4" />
            Create Bot
          </Button>
          {runningBots.length > 0 && (
            <Button
              variant="destructive"
              onClick={() => setKillAllDialogOpen(true)}
            >
              <Skull className="mr-2 h-4 w-4" />
              Kill All ({runningBots.length})
            </Button>
          )}
        </div>
      </div>

      {/* WebSocket connection status */}
      {!connected && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            WebSocket disconnected. Real-time updates unavailable.
          </AlertDescription>
        </Alert>
      )}

      {/* Create Bot Form */}
      {createFormOpen && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Bot</CardTitle>
            <CardDescription>
              Configure a new trading bot
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="bot-name">Bot Name</Label>
                <Input
                  id="bot-name"
                  placeholder="My Trading Bot"
                  value={createFormData.name}
                  onChange={(e) =>
                    setCreateFormData({ ...createFormData, name: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="strategy-id">Strategy</Label>
                <Select
                  value={createFormData.strategy_id}
                  onValueChange={(value) =>
                    setCreateFormData({ ...createFormData, strategy_id: value })
                  }
                >
                  <SelectTrigger id="strategy-id">
                    <SelectValue placeholder="Select strategy" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="123e4567-e89b-12d3-a456-426614174000">
                      Scalping Strategy
                    </SelectItem>
                    <SelectItem value="234e5678-e89b-12d3-a456-426614174001">
                      Trend Following
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="mode">Mode</Label>
                <Select
                  value={createFormData.mode}
                  onValueChange={(value) =>
                    setCreateFormData({
                      ...createFormData,
                      mode: value as 'live' | 'paper' | 'simulation',
                    })
                  }
                >
                  <SelectTrigger id="mode">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="paper">Paper Trading</SelectItem>
                    <SelectItem value="live">Live Trading</SelectItem>
                    <SelectItem value="simulation">Simulation</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="apex-account">Apex Account (Optional)</Label>
                <Select
                  value={createFormData.apex_account_id || ''}
                  onValueChange={(value) =>
                    setCreateFormData({
                      ...createFormData,
                      apex_account_id: value || undefined,
                    })
                  }
                >
                  <SelectTrigger id="apex-account">
                    <SelectValue placeholder="Select account" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="789e0123-e89b-12d3-a456-426614174000">
                      PA-12345678
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => createBotMutation.mutate(createFormData)}
                disabled={
                  !createFormData.name ||
                  !createFormData.strategy_id ||
                  createBotMutation.isPending
                }
              >
                Create Bot
              </Button>
              <Button variant="outline" onClick={() => setCreateFormOpen(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bots List */}
      <Card>
        <CardHeader>
          <CardTitle>Bots</CardTitle>
          <CardDescription>
            {bots.length} bot{bots.length !== 1 ? 's' : ''} configured
          </CardDescription>
        </CardHeader>
        <CardContent>
          {botsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading bots...
            </div>
          ) : bots.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No bots created. Create your first bot to start trading.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Apex Account</TableHead>
                  <TableHead>Heartbeat</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bots.map((bot) => (
                  <TableRow
                    key={bot.id}
                    className={selectedBot?.id === bot.id ? 'bg-muted' : ''}
                    onClick={() => setSelectedBot(bot)}
                  >
                    <TableCell className="font-medium">{bot.name}</TableCell>
                    <TableCell>
                      <StatusBadge status={bot.status} />
                    </TableCell>
                    <TableCell className="capitalize">{bot.mode}</TableCell>
                    <TableCell>
                      {bot.apex_account_id
                        ? bot.apex_account_id.slice(0, 8)
                        : '-'}
                    </TableCell>
                    <TableCell>
                      <HeartbeatIndicator lastHeartbeat={bot.last_heartbeat} />
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            startBotMutation.mutate(bot.id);
                          }}
                          disabled={
                            bot.status === 'running' ||
                            bot.status === 'killed' ||
                            startBotMutation.isPending
                          }
                        >
                          <PlayCircle className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            stopBotMutation.mutate(bot.id);
                          }}
                          disabled={
                            bot.status !== 'running' || stopBotMutation.isPending
                          }
                        >
                          <Square className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            setBotToKill(bot.id);
                            setKillDialogOpen(true);
                          }}
                          disabled={bot.status === 'killed'}
                        >
                          <Skull className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* State Log Timeline */}
      {selectedBot && (
        <Card>
          <CardHeader>
            <CardTitle>State Log Timeline - {selectedBot.name}</CardTitle>
            <CardDescription>
              Bot state transitions and reasons
            </CardDescription>
          </CardHeader>
          <CardContent>
            {stateLogData?.states && stateLogData.states.length > 0 ? (
              <div className="space-y-4">
                {stateLogData.states.map((entry, index) => (
                  <div key={index} className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                        <Clock className="h-4 w-4 text-primary-foreground" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium capitalize">{entry.from}</span>
                        <span>→</span>
                        <span className="font-medium capitalize">{entry.to}</span>
                        <span className="text-sm text-muted-foreground">
                          {new Date(entry.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {entry.reason}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No state transitions recorded
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Kill Bot Confirmation Dialog */}
      <AlertDialog open={killDialogOpen} onOpenChange={setKillDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will immediately kill the bot and close all open positions. This
              action is irreversible.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (botToKill) {
                  killBotMutation.mutate(botToKill);
                }
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Kill Bot
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Kill All Bots Confirmation Dialog */}
      <AlertDialog open={killAllDialogOpen} onOpenChange={setKillAllDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Kill All Running Bots?</AlertDialogTitle>
            <AlertDialogDescription>
              This will immediately kill all {runningBots.length} running bots and
              close all open positions. This action is irreversible.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => killAllBotsMutation.mutate()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Kill All Bots
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default BotManagement;
