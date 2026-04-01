/**
 * Bot Management Page (AUT-354)
 *
 * Main page for managing trading bots:
 * - Display grid of bot cards with real-time status
 * - Create new bots
 * - Start/Stop/Kill operations
 * - State transition history
 * - WebSocket integration for live updates
 */

import React, { useState } from 'react';
import { BotCard } from '@/client/components/bots/BotCard';
import { CreateBotPanel } from '@/client/components/bots/CreateBotPanel';
import { KillConfirmModal } from '@/client/components/bots/KillConfirmModal';
import { useBotManagement } from '@/hooks/useBotManagement';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAuth } from '@/state/app';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// Mock data for strategies and apex accounts (replace with real API)
const MOCK_STRATEGIES = [
  { id: '123e4567-e89b-12d3-a456-426614174000', name: 'Scalping Strategy v1.0' },
  { id: '234e5678-e89b-12d3-a456-426614174001', name: 'Trend Following v2.1' },
  { id: '345e6789-e89b-12d3-a456-426614174002', name: 'Mean Reversion Pro' },
];

const MOCK_APEX_ACCOUNTS = [
  { id: '789e0123-e89b-12d3-a456-426614174000', name: 'PA-12345 ($50k)' },
  { id: '890e1234-e89b-12d3-a456-426614174001', name: 'PA-67890 ($150k)' },
  { id: '901e2345-e89b-12d3-a456-426614174002', name: 'PA-11111 ($25k)' },
];

const Bot: React.FC = () => {
  const { user } = useAuth();
  const {
    bots,
    stateLogs,
    isLoading,
    error,
    fetchBots,
    startBot,
    stopBot,
    killBot,
    createBot,
  } = useBotManagement();

  const [killModalOpen, setKillModalOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState<{
    id: string;
    name: string;
  } | null>(null);

  // Check if user has trader or admin role
  const canTrade = user?.role === 'trader' || user?.role === 'admin';

  if (!canTrade) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              Access Restricted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Trading bot access is restricted to traders and administrators.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  /**
   * Handle kill button click - open modal
   */
  const handleKillClick = (botId: string) => {
    const bot = bots.find((b) => b.id === botId);
    if (bot) {
      setSelectedBot({ id: bot.id, name: bot.name });
      setKillModalOpen(true);
    }
  };

  /**
   * Handle kill confirmation - execute kill with reason
   */
  const handleKillConfirm = async (reason: string) => {
    if (selectedBot) {
      await killBot(selectedBot.id, reason);
      setKillModalOpen(false);
      setSelectedBot(null);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Bot Management</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and control your trading bots in real-time
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchBots}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bots Grid - 2 columns */}
        <div className="lg:col-span-2 space-y-4">
          {bots.length === 0 && !isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 border-2 border-dashed rounded-lg">
              <p className="text-muted-foreground text-center">
                No bots found. Create your first bot to get started.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {bots.map((bot) => (
                <BotCard
                  key={bot.id}
                  bot={bot}
                  stateLog={stateLogs[bot.id] || []}
                  onStart={startBot}
                  onStop={stopBot}
                  onKill={handleKillClick}
                  isLoading={isLoading}
                />
              ))}
            </div>
          )}
        </div>

        {/* Create Bot Panel - 1 column */}
        <div className="lg:col-span-1">
          <CreateBotPanel
            strategies={MOCK_STRATEGIES}
            apexAccounts={MOCK_APEX_ACCOUNTS}
            onCreate={createBot}
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Kill Confirmation Modal */}
      {selectedBot && (
        <KillConfirmModal
          open={killModalOpen}
          onOpenChange={setKillModalOpen}
          botName={selectedBot.name}
          onConfirm={handleKillConfirm}
          isLoading={isLoading}
        />
      )}
    </div>
  );
};

export default Bot;
