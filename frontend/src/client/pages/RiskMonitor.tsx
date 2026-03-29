/**
 * Risk Monitor Page
 *
 * Safety-critical page for real-time risk monitoring and kill switch controls
 */

import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, AlertCircle, XCircle, Activity, Shield, Zap, StopCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { useNQHubWebSocket } from '@/hooks/useNQHubWebSocket';
import { apiClient } from '@/services/api';
import { cn } from '@/lib/utils';

interface RiskMetrics {
  bot_id: string;
  bot_name: string;
  daily_loss_usd: number;
  max_daily_loss_usd: number;
  trailing_drawdown_usd: number;
  trailing_threshold_usd: number;
  circuit_breaker_status: 'ACTIVE' | 'TRIGGERED';
  circuit_breaker_reason?: string;
  circuit_breaker_timestamp?: string;
}

interface RiskAlert {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'CRITICAL';
  message: string;
  bot_id?: string;
}

interface RiskConfig {
  max_daily_loss_usd: number;
  max_trailing_drawdown_usd: number;
  max_contracts: number;
  max_orders_per_minute: number;
  news_blackout_minutes: number;
  apex_consistency_pct: number;
  kill_switch_enabled: boolean;
}

interface Bot {
  id: string;
  name: string;
  status: 'stopped' | 'running' | 'killed' | 'error';
  mode: 'live' | 'paper' | 'simulation';
}

export default function RiskMonitor() {
  const { connected, subscribe, unsubscribe, lastMessage } = useNQHubWebSocket();
  const [bots, setBots] = useState<Bot[]>([]);
  const [riskMetrics, setRiskMetrics] = useState<Map<string, RiskMetrics>>(new Map());
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [riskConfig, setRiskConfig] = useState<RiskConfig | null>(null);
  const [killBotModal, setKillBotModal] = useState<{ open: boolean; bot: Bot | null }>({
    open: false,
    bot: null
  });
  const [killAllModal, setKillAllModal] = useState(false);
  const [isKilling, setIsKilling] = useState(false);
  const alertsEndRef = useRef<HTMLDivElement>(null);

  // Subscribe to WebSocket channels on mount
  useEffect(() => {
    const channels = ['risk', 'bot', 'portfolio'];
    subscribe(channels);

    // Load initial data
    loadBots();
    loadRiskConfig();
    loadRiskStatus();

    return () => {
      unsubscribe(channels);
    };
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.risk) {
      const msg = lastMessage.risk;

      switch (msg.event) {
        case 'daily_loss_update':
          updateMetrics(msg.data.bot_id, {
            daily_loss_usd: msg.data.daily_loss_usd,
            max_daily_loss_usd: msg.data.limit_usd
          });
          break;

        case 'trailing_drawdown_update':
          updateMetrics(msg.data.bot_id, {
            trailing_drawdown_usd: msg.data.drawdown_usd,
            trailing_threshold_usd: msg.data.threshold_usd
          });
          break;

        case 'circuit_breaker_triggered':
          updateMetrics(msg.data.bot_id, {
            circuit_breaker_status: 'TRIGGERED',
            circuit_breaker_reason: msg.data.reason,
            circuit_breaker_timestamp: msg.data.timestamp
          });
          addAlert('CRITICAL', `Circuit breaker triggered for ${msg.data.bot_id}: ${msg.data.reason}`, msg.data.bot_id);
          break;

        case 'kill_switch_activated':
          updateBotStatus(msg.data.bot_id, 'killed');
          addAlert('CRITICAL', `Kill switch activated for ${msg.data.bot_id}: ${msg.data.reason}`, msg.data.bot_id);
          break;

        case 'risk_alert':
          addAlert(msg.data.level, msg.data.message, msg.data.bot_id);
          break;
      }
    }

    if (lastMessage.bot) {
      const msg = lastMessage.bot;
      if (msg.event === 'botStatusChanged') {
        updateBotStatus(msg.data.bot_id, msg.data.status);
      }
    }
  }, [lastMessage]);

  // Auto-scroll alerts to bottom
  useEffect(() => {
    // Check if scrollIntoView is available (not in test environment)
    if (alertsEndRef.current && typeof alertsEndRef.current.scrollIntoView === 'function') {
      alertsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [alerts]);

  const loadBots = async () => {
    try {
      const response = await apiClient.get('/bots');
      setBots(response.bots);

      // Initialize risk metrics for each bot
      const newMetrics = new Map<string, RiskMetrics>();
      response.bots.forEach((bot: Bot) => {
        newMetrics.set(bot.id, {
          bot_id: bot.id,
          bot_name: bot.name,
          daily_loss_usd: 0,
          max_daily_loss_usd: 2500,
          trailing_drawdown_usd: 0,
          trailing_threshold_usd: 2500,
          circuit_breaker_status: 'ACTIVE'
        });
      });
      setRiskMetrics(newMetrics);
    } catch (error) {
      console.error('Failed to load bots:', error);
    }
  };

  const loadRiskConfig = async () => {
    try {
      const response = await apiClient.get('/risk/config');
      setRiskConfig(response);
    } catch (error) {
      console.error('Failed to load risk config:', error);
    }
  };

  const loadRiskStatus = async () => {
    try {
      const response = await apiClient.get('/risk/status');
      // Update metrics with current status
      if (response.bot_metrics) {
        const newMetrics = new Map(riskMetrics);
        Object.entries(response.bot_metrics).forEach(([botId, metrics]: [string, any]) => {
          if (newMetrics.has(botId)) {
            newMetrics.set(botId, { ...newMetrics.get(botId)!, ...metrics });
          }
        });
        setRiskMetrics(newMetrics);
      }
    } catch (error) {
      console.error('Failed to load risk status:', error);
    }
  };

  const updateMetrics = (botId: string, updates: Partial<RiskMetrics>) => {
    setRiskMetrics(prev => {
      const newMetrics = new Map(prev);
      const current = newMetrics.get(botId);
      if (current) {
        newMetrics.set(botId, { ...current, ...updates });
      }
      return newMetrics;
    });
  };

  const updateBotStatus = (botId: string, status: Bot['status']) => {
    setBots(prev => prev.map(bot =>
      bot.id === botId ? { ...bot, status } : bot
    ));
  };

  const addAlert = (level: RiskAlert['level'], message: string, botId?: string) => {
    const newAlert: RiskAlert = {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      level,
      message,
      bot_id: botId
    };
    setAlerts(prev => [...prev, newAlert]);
  };

  const handleKillBot = async (bot: Bot) => {
    setIsKilling(true);
    try {
      await apiClient.post(`/bots/${bot.id}/kill`, {
        reason: 'Manual kill from Risk Monitor',
        close_positions: true
      });
      updateBotStatus(bot.id, 'killed');
      addAlert('WARNING', `Bot ${bot.name} has been killed`, bot.id);
      setKillBotModal({ open: false, bot: null });
    } catch (error) {
      console.error('Failed to kill bot:', error);
      addAlert('CRITICAL', `Failed to kill bot ${bot.name}`, bot.id);
    } finally {
      setIsKilling(false);
    }
  };

  const handleKillAll = async () => {
    setIsKilling(true);
    try {
      await apiClient.post('/bots/kill-all', {
        reason: 'Emergency stop - Manual kill all from Risk Monitor',
        close_positions: true,
        confirm: 'KILL_ALL_BOTS'
      });

      // Update all bot statuses
      setBots(prev => prev.map(bot => ({ ...bot, status: 'killed' as const })));
      addAlert('CRITICAL', 'EMERGENCY STOP: All bots have been killed');
      setKillAllModal(false);
    } catch (error) {
      console.error('Failed to kill all bots:', error);
      addAlert('CRITICAL', 'EMERGENCY STOP FAILED - Kill all bots operation failed!');
    } finally {
      setIsKilling(false);
    }
  };

  const clearAlerts = () => {
    // Only clear non-critical alerts
    setAlerts(prev => prev.filter(alert => alert.level === 'CRITICAL'));
  };

  const getMeterColor = (percentage: number) => {
    if (percentage < 50) return 'text-green-600';
    if (percentage < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProgressColor = (percentage: number) => {
    if (percentage < 50) return 'bg-green-600';
    if (percentage < 80) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  return (
    <div className="container mx-auto p-4 space-y-4 max-w-7xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="w-8 h-8 text-red-600" />
            Risk Monitor
          </h1>
          <p className="text-muted-foreground">Real-time risk monitoring and emergency controls</p>
        </div>
        <div className="flex items-center gap-2">
          {connected ? (
            <Badge variant="outline" className="bg-green-100 text-green-800">
              <Activity className="w-3 h-3 mr-1" />
              Connected
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-red-100 text-red-800">
              <XCircle className="w-3 h-3 mr-1" />
              Disconnected
            </Badge>
          )}
        </div>
      </div>

      {/* Risk Meters Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {Array.from(riskMetrics.values()).map(metrics => {
          const bot = bots.find(b => b.id === metrics.bot_id);
          const dailyLossPct = (metrics.daily_loss_usd / metrics.max_daily_loss_usd) * 100;
          const drawdownPct = (metrics.trailing_drawdown_usd / metrics.trailing_threshold_usd) * 100;

          return (
            <Card key={metrics.bot_id} className="relative">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="text-lg">{metrics.bot_name}</span>
                  <Badge
                    variant={bot?.status === 'running' ? 'default' : 'secondary'}
                    className={cn(
                      bot?.status === 'killed' && 'bg-red-600 text-white',
                      bot?.status === 'error' && 'bg-orange-600 text-white'
                    )}
                  >
                    {bot?.status?.toUpperCase()}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Daily Loss Meter */}
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Daily Loss</span>
                    <span className={getMeterColor(dailyLossPct)}>
                      ${metrics.daily_loss_usd.toFixed(2)} / ${metrics.max_daily_loss_usd.toFixed(2)}
                    </span>
                  </div>
                  <Progress
                    value={dailyLossPct}
                    className="h-2"
                    indicatorClassName={getProgressColor(dailyLossPct)}
                  />
                  <div className="text-xs text-muted-foreground text-right">
                    {dailyLossPct.toFixed(1)}% of limit
                  </div>
                </div>

                {/* Trailing Drawdown Meter */}
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Trailing Drawdown</span>
                    <span className={getMeterColor(drawdownPct)}>
                      ${metrics.trailing_drawdown_usd.toFixed(2)} / ${metrics.trailing_threshold_usd.toFixed(2)}
                    </span>
                  </div>
                  <Progress
                    value={drawdownPct}
                    className="h-2"
                    indicatorClassName={getProgressColor(drawdownPct)}
                  />
                  <div className="text-xs text-muted-foreground text-right">
                    {drawdownPct.toFixed(1)}% proximity to Apex threshold
                  </div>
                </div>

                {/* Circuit Breaker Status */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="text-sm font-medium">Circuit Breaker</span>
                  {metrics.circuit_breaker_status === 'TRIGGERED' ? (
                    <Badge variant="destructive" className="animate-pulse">
                      <Zap className="w-3 h-3 mr-1" />
                      TRIGGERED
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="bg-green-100 text-green-800">
                      <Shield className="w-3 h-3 mr-1" />
                      ACTIVE
                    </Badge>
                  )}
                </div>
                {metrics.circuit_breaker_reason && (
                  <Alert className="mt-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      {metrics.circuit_breaker_reason}
                      <br />
                      <span className="text-muted-foreground">
                        {new Date(metrics.circuit_breaker_timestamp!).toLocaleString()}
                      </span>
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Kill Switch Controls */}
      <Card className="border-red-500 bg-red-50 dark:bg-red-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="w-5 h-5" />
            KILL SWITCHES
          </CardTitle>
          <CardDescription>
            Emergency stop controls - Use with extreme caution
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Individual Bot Kill Switches */}
          <div className="space-y-2">
            {bots.filter(bot => bot.status === 'running').map(bot => (
              <div key={bot.id} className="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-gray-950">
                <div className="flex items-center gap-3">
                  <span className="font-medium">{bot.name}</span>
                  <Badge variant="outline">{bot.mode}</Badge>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setKillBotModal({ open: true, bot })}
                  className="bg-red-600 hover:bg-red-700"
                >
                  <StopCircle className="w-4 h-4 mr-1" />
                  KILL BOT
                </Button>
              </div>
            ))}
            {bots.filter(bot => bot.status === 'running').length === 0 && (
              <div className="text-center py-4 text-muted-foreground">
                No running bots
              </div>
            )}
          </div>

          <Separator />

          {/* Kill All Button */}
          <div className="flex justify-center pt-2">
            <Button
              variant="destructive"
              size="lg"
              onClick={() => setKillAllModal(true)}
              className="bg-red-700 hover:bg-red-800 animate-pulse border-2 border-red-900"
              disabled={bots.filter(bot => bot.status === 'running').length === 0}
            >
              <XCircle className="w-5 h-5 mr-2" />
              🔴🔴 KILL ALL BOTS — EMERGENCY STOP 🔴🔴
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Real-Time Alerts Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Real-Time Alerts</span>
              <Button
                variant="outline"
                size="sm"
                onClick={clearAlerts}
                disabled={alerts.filter(a => a.level !== 'CRITICAL').length === 0}
              >
                Clear
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] w-full pr-4">
              <div className="space-y-2">
                {alerts.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No alerts
                  </div>
                ) : (
                  alerts.map(alert => (
                    <Alert
                      key={alert.id}
                      className={cn(
                        alert.level === 'CRITICAL' && 'border-red-600 bg-red-50 dark:bg-red-950/50',
                        alert.level === 'WARNING' && 'border-yellow-600 bg-yellow-50 dark:bg-yellow-950/50'
                      )}
                    >
                      {alert.level === 'CRITICAL' ? (
                        <XCircle className="h-4 w-4 text-red-600" />
                      ) : alert.level === 'WARNING' ? (
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                      ) : (
                        <AlertCircle className="h-4 w-4" />
                      )}
                      <AlertTitle className="text-xs">
                        {new Date(alert.timestamp).toLocaleTimeString()} - {alert.level}
                      </AlertTitle>
                      <AlertDescription className="text-xs">
                        {alert.message}
                      </AlertDescription>
                    </Alert>
                  ))
                )}
                <div ref={alertsEndRef} />
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Risk Config Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Risk Configuration</span>
              <Button variant="outline" size="sm" disabled>
                Edit in Settings
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {riskConfig ? (
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-muted-foreground">Max Daily Loss</span>
                  <span className="font-medium">${riskConfig.max_daily_loss_usd.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-muted-foreground">Max Trailing Drawdown</span>
                  <span className="font-medium">${riskConfig.max_trailing_drawdown_usd.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-muted-foreground">Max Contracts</span>
                  <span className="font-medium">{riskConfig.max_contracts}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-muted-foreground">Max Orders/Minute</span>
                  <span className="font-medium">{riskConfig.max_orders_per_minute}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-muted-foreground">News Blackout</span>
                  <span className="font-medium">{riskConfig.news_blackout_minutes} min</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-muted-foreground">Apex Consistency</span>
                  <span className="font-medium">{riskConfig.apex_consistency_pct}%</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-sm text-muted-foreground">Kill Switch</span>
                  <Badge variant={riskConfig.kill_switch_enabled ? 'default' : 'secondary'}>
                    {riskConfig.kill_switch_enabled ? 'ENABLED' : 'DISABLED'}
                  </Badge>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Loading configuration...
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Kill Bot Confirmation Modal */}
      <Dialog open={killBotModal.open} onOpenChange={(open) => !isKilling && setKillBotModal({ open, bot: killBotModal.bot })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Confirm Kill Bot
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to kill <strong>{killBotModal.bot?.name}</strong>?
              This will immediately stop the bot and close all open positions.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setKillBotModal({ open: false, bot: null })}
              disabled={isKilling}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => killBotModal.bot && handleKillBot(killBotModal.bot)}
              disabled={isKilling}
            >
              {isKilling ? 'Killing...' : 'Kill Bot'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Kill All Confirmation Modal */}
      <Dialog open={killAllModal} onOpenChange={(open) => !isKilling && setKillAllModal(open)}>
        <DialogContent className="border-red-600">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600 text-xl">
              <XCircle className="w-6 h-6" />
              ⚠️ EMERGENCY STOP CONFIRMATION ⚠️
            </DialogTitle>
            <DialogDescription className="space-y-2 pt-4">
              <Alert className="border-red-600 bg-red-50 dark:bg-red-950/50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertTitle>CRITICAL ACTION</AlertTitle>
                <AlertDescription>
                  This will IMMEDIATELY:
                  <ul className="list-disc list-inside mt-2">
                    <li>Kill ALL running bots</li>
                    <li>Close ALL open positions</li>
                    <li>Cancel ALL pending orders</li>
                    <li>Halt ALL trading activity</li>
                  </ul>
                </AlertDescription>
              </Alert>
              <p className="font-semibold">
                Are you absolutely sure you want to proceed with the EMERGENCY STOP?
              </p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setKillAllModal(false)}
              disabled={isKilling}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleKillAll}
              disabled={isKilling}
              className="bg-red-700 hover:bg-red-800"
            >
              {isKilling ? 'KILLING ALL...' : '🔴 CONFIRM EMERGENCY STOP 🔴'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}