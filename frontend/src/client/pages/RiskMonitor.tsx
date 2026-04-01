import React, { useEffect, useState } from 'react';
import { GlobalKillSwitchBar } from '@/components/risk/GlobalKillSwitchBar';
import { RiskGauge } from '@/components/risk/RiskGauge';
import { KillSwitchButton } from '@/components/risk/KillSwitchButton';
import { CircuitBreakerStatus } from '@/components/risk/CircuitBreakerStatus';
import { RiskEventFeed } from '@/components/risk/RiskEventFeed';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface BotRiskData {
  bot_id: string;
  bot_name: string;
  account_balance: number;
  daily_pnl: number;
  max_daily_loss: number;
  trailing_threshold: number;
  trailing_threshold_remaining: number;
  circuit_breakers: Array<{
    name: string;
    active: boolean;
    threshold: number;
    current_value: number;
  }>;
  risk_events: Array<{
    ts: string;
    check_name: string;
    result: 'PASSED' | 'REJECTED';
    reason?: string;
  }>;
}

export default function RiskMonitor() {
  const [bots, setBots] = useState<BotRiskData[]>([]);
  const [killSwitchAlert, setKillSwitchAlert] = useState<{ show: boolean; data?: any }>({ show: false });

  const { connected, latestRiskCheck, latestKillSwitch } = useWebSocket({
    autoSubscribe: ['risk', 'bot'],
    autoConnect: false,
  });

  useEffect(() => {
    loadBotRiskData();
  }, []);

  useEffect(() => {
    if (latestKillSwitch) {
      setKillSwitchAlert({ show: true, data: latestKillSwitch });
    }
  }, [latestKillSwitch]);

  useEffect(() => {
    if (latestRiskCheck && latestRiskCheck.bot_id) {
      setBots((prevBots) =>
        prevBots.map((bot) => {
          if (bot.bot_id === latestRiskCheck.bot_id) {
            return {
              ...bot,
              risk_events: [
                { ts: latestRiskCheck.ts, check_name: latestRiskCheck.check_name, result: latestRiskCheck.result, reason: latestRiskCheck.reason },
                ...bot.risk_events.slice(0, 4),
              ],
            };
          }
          return bot;
        })
      );
    }
  }, [latestRiskCheck]);

  const loadBotRiskData = async () => {
    setBots([
      { bot_id: 'bot-001', bot_name: 'NQ Scalper Alpha', account_balance: 24650.0, daily_pnl: -350.0, max_daily_loss: 1000.0, trailing_threshold: 1500.0, trailing_threshold_remaining: 1150.0, circuit_breakers: [], risk_events: [] },
    ]);
  };

  const handleKillAll = async (reason: string) => {
    console.log('Kill all bots:', reason);
  };

  const handleKillBot = async (botId: string, reason: string) => {
    console.log('Kill bot:', botId, reason);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <GlobalKillSwitchBar onKillAll={handleKillAll} />
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Risk Monitor</h1>
          <div className="flex items-center space-x-2">
            <div className={'w-3 h-3 rounded-full ' + (connected ? 'bg-green-500' : 'bg-red-500')} />
            <span className="text-sm text-gray-600 dark:text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {bots.map((bot) => (
            <Card key={bot.bot_id} className="shadow-lg">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{bot.bot_name}</CardTitle>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200">🟢 RUNNING</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <RiskGauge label="Daily Loss" value={bot.daily_pnl} limit={bot.max_daily_loss} format="currency" />
                  <RiskGauge label="Trailing Drawdown" value={bot.trailing_threshold - bot.trailing_threshold_remaining} limit={bot.trailing_threshold} format="currency" />
                </div>
                <CircuitBreakerStatus circuitBreakers={bot.circuit_breakers} />
                <RiskEventFeed events={bot.risk_events} />
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <KillSwitchButton botId={bot.bot_id} botName={bot.bot_name} onKill={handleKillBot} className="w-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      <Dialog open={killSwitchAlert.show} onOpenChange={(show) => setKillSwitchAlert({ show })}>
        <DialogContent className="sm:max-w-md border-4 border-red-600">
          <DialogHeader>
            <DialogTitle className="text-red-600 text-2xl flex items-center space-x-2">
              <span className="text-3xl animate-pulse">🚨</span>
              <span>KILL SWITCH ACTIVATED</span>
            </DialogTitle>
            <DialogDescription className="text-lg">Emergency shutdown triggered by {killSwitchAlert.data?.triggered_by || 'system'}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-md p-4">
              <p className="text-sm font-semibold text-red-800 dark:text-red-200 mb-2">Reason:</p>
              <p className="text-sm text-red-700 dark:text-red-300">{killSwitchAlert.data?.reason || 'No reason provided'}</p>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Positions Closed:</span>
                <span className="ml-2 font-semibold">{killSwitchAlert.data?.positions_closed || 0}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Orders Cancelled:</span>
                <span className="ml-2 font-semibold">{killSwitchAlert.data?.orders_cancelled || 0}</span>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
