/**
 * Settings Page - AUT-359
 * 4 sections: Apex Accounts, Credentials, Schedules, Alert Notifications
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Settings as SettingsIcon,
  Bell,
  Clock,
  Shield,
  Check,
  X,
  Plus,
  Edit,
  TestTube,
  CircleDot,
} from 'lucide-react';
import { useAuth } from '@/state/app';
import { toast } from 'sonner';

// Apex account size presets with auto-fill values
const APEX_PRESETS = {
  '25000': { threshold: 1250, max_contracts: 5 },
  '50000': { threshold: 2500, max_contracts: 10 },
  '100000': { threshold: 5000, max_contracts: 20 },
  '250000': { threshold: 12500, max_contracts: 50 },
  '300000': { threshold: 15000, max_contracts: 60 },
};

interface ApexAccount {
  id: string;
  account_name: string;
  account_size_usd: number;
  trailing_threshold_usd: number;
  max_daily_loss_usd: number;
  max_contracts: number;
  consistency_pct: number;
  news_blackout_minutes: number;
  status: 'connected' | 'disconnected' | 'testing';
}

interface Credentials {
  rithmic_username: 'configured' | 'not_configured';
  rithmic_password: 'configured' | 'not_configured';
  rithmic_server: string;
  sendgrid_api_key: 'configured' | 'not_configured';
  telegram_bot_token: 'configured' | 'not_configured';
  telegram_chat_id: string;
}

interface TradingSchedule {
  ny_am_session: boolean;
  ny_pm_session: boolean;
  london_session: boolean;
  asia_session: boolean;
}

interface NotificationConfig {
  [event: string]: {
    telegram: boolean;
    email: boolean;
    in_app: boolean;
  };
}

const Settings: React.FC = () => {
  const { token } = useAuth();

  // State for Apex Accounts
  const [apexAccounts, setApexAccounts] = useState<ApexAccount[]>([]);
  const [isAddingAccount, setIsAddingAccount] = useState(false);
  const [editingAccount, setEditingAccount] = useState<ApexAccount | null>(null);
  const [newAccount, setNewAccount] = useState<Partial<ApexAccount>>({
    account_name: '',
    account_size_usd: 50000,
    trailing_threshold_usd: 2500,
    max_daily_loss_usd: 1500,
    max_contracts: 10,
    consistency_pct: 30,
    news_blackout_minutes: 5,
  });

  // State for Credentials
  const [credentials, setCredentials] = useState<Credentials>({
    rithmic_username: 'not_configured',
    rithmic_password: 'not_configured',
    rithmic_server: 'PAPER_TRADING',
    sendgrid_api_key: 'not_configured',
    telegram_bot_token: 'not_configured',
    telegram_chat_id: '',
  });
  const [credentialModal, setCredentialModal] = useState<{
    open: boolean;
    key: string;
    value: string;
  }>({ open: false, key: '', value: '' });

  // State for Trading Schedules
  const [schedules, setSchedules] = useState<TradingSchedule>({
    ny_am_session: true,
    ny_pm_session: true,
    london_session: false,
    asia_session: false,
  });

  // State for Alert Notifications
  const [notifications, setNotifications] = useState<NotificationConfig>({
    kill_switch_activated: { telegram: true, email: true, in_app: true },
    circuit_breaker: { telegram: true, email: true, in_app: true },
    daily_loss_warning: { telegram: false, email: false, in_app: true },
    daily_loss_critical: { telegram: true, email: false, in_app: true },
    trailing_drawdown_warning: { telegram: false, email: false, in_app: true },
    trailing_drawdown_critical: { telegram: true, email: false, in_app: true },
    trade_filled: { telegram: false, email: false, in_app: false },
    bot_heartbeat_lost: { telegram: true, email: true, in_app: true },
  });

  // Fetch initial data
  useEffect(() => {
    fetchApexAccounts();
    fetchCredentials();
    fetchSchedules();
    fetchNotifications();
  }, []);

  const fetchApexAccounts = async () => {
    try {
      const response = await fetch('/api/v1/settings/apex-accounts', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setApexAccounts(data.accounts || []);
      }
    } catch (error) {
      console.error('Error fetching apex accounts:', error);
    }
  };

  const fetchCredentials = async () => {
    try {
      const response = await fetch('/api/v1/settings/credentials', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setCredentials(data);
      }
    } catch (error) {
      console.error('Error fetching credentials:', error);
    }
  };

  const fetchSchedules = async () => {
    try {
      const response = await fetch('/api/v1/settings/schedules', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setSchedules(data);
      }
    } catch (error) {
      console.error('Error fetching schedules:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await fetch('/api/v1/settings/notifications', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  // Auto-fill handler for Apex account size
  const handleAccountSizeChange = (size: string) => {
    const sizeNum = parseInt(size);
    const preset = APEX_PRESETS[size as keyof typeof APEX_PRESETS];

    if (editingAccount) {
      setEditingAccount({
        ...editingAccount,
        account_size_usd: sizeNum,
        trailing_threshold_usd: preset.threshold,
        max_contracts: preset.max_contracts,
      });
    } else {
      setNewAccount({
        ...newAccount,
        account_size_usd: sizeNum,
        trailing_threshold_usd: preset.threshold,
        max_contracts: preset.max_contracts,
      });
    }
  };

  const handleSaveAccount = async () => {
    const accountData = editingAccount || newAccount;
    const endpoint = editingAccount
      ? `/api/v1/settings/apex-accounts/${editingAccount.id}`
      : '/api/v1/settings/apex-accounts';
    const method = editingAccount ? 'PUT' : 'POST';

    try {
      const response = await fetch(endpoint, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(accountData),
      });

      if (response.ok) {
        toast.success(editingAccount ? 'Account updated' : 'Account created');
        fetchApexAccounts();
        setIsAddingAccount(false);
        setEditingAccount(null);
        setNewAccount({
          account_name: '',
          account_size_usd: 50000,
          trailing_threshold_usd: 2500,
          max_daily_loss_usd: 1500,
          max_contracts: 10,
          consistency_pct: 30,
          news_blackout_minutes: 5,
        });
      }
    } catch (error) {
      console.error('Error saving account:', error);
      toast.error('Failed to save account');
    }
  };

  const handleTestAccount = async (accountId: string) => {
    try {
      const accountIndex = apexAccounts.findIndex((a) => a.id === accountId);
      if (accountIndex !== -1) {
        const updatedAccounts = [...apexAccounts];
        updatedAccounts[accountIndex] = { ...updatedAccounts[accountIndex], status: 'testing' };
        setApexAccounts(updatedAccounts);
      }

      const response = await fetch(`/api/v1/accounts/${accountId}/test`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        const updatedAccounts = [...apexAccounts];
        const idx = updatedAccounts.findIndex((a) => a.id === accountId);
        if (idx !== -1) {
          updatedAccounts[idx] = { ...updatedAccounts[idx], status: data.status };
          setApexAccounts(updatedAccounts);
        }
        toast.success(`Connection ${data.status}`);
      }
    } catch (error) {
      console.error('Error testing account:', error);
      toast.error('Connection test failed');
    }
  };

  const handleUpdateCredential = async () => {
    try {
      const response = await fetch(`/api/v1/settings/credentials/${credentialModal.key}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ value: credentialModal.value }),
      });

      if (response.ok) {
        toast.success('Credential updated');
        fetchCredentials();
        setCredentialModal({ open: false, key: '', value: '' });
      }
    } catch (error) {
      console.error('Error updating credential:', error);
      toast.error('Failed to update credential');
    }
  };

  const handleSaveSchedules = async () => {
    try {
      const response = await fetch('/api/v1/settings/schedules', {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(schedules),
      });

      if (response.ok) {
        toast.success('Schedules updated');
      }
    } catch (error) {
      console.error('Error saving schedules:', error);
      toast.error('Failed to save schedules');
    }
  };

  const handleSaveNotifications = async () => {
    try {
      const response = await fetch('/api/v1/settings/notifications', {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(notifications),
      });

      if (response.ok) {
        toast.success('Notifications updated');
      }
    } catch (error) {
      console.error('Error saving notifications:', error);
      toast.error('Failed to save notifications');
    }
  };

  const handleTestAlert = async () => {
    try {
      const response = await fetch('/api/v1/settings/test-alert', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Test alert sent via: ${data.channels.join(', ')}`);
      }
    } catch (error) {
      console.error('Error testing alert:', error);
      toast.error('Failed to send test alert');
    }
  };

  const accountToEdit = editingAccount || newAccount;

  return (
    <div className="flex-1 space-y-6 p-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage system configuration and trading parameters</p>
      </div>

      <Tabs defaultValue="apex" className="space-y-4">
        <TabsList>
          <TabsTrigger value="apex">Apex Accounts</TabsTrigger>
          <TabsTrigger value="credentials">Credentials</TabsTrigger>
          <TabsTrigger value="schedules">Schedules</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        {/* Section 1: Apex Accounts */}
        <TabsContent value="apex" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <SettingsIcon className="h-5 w-5" />
                  Apex Funded Accounts
                </span>
                <Button
                  size="sm"
                  onClick={() => setIsAddingAccount(true)}
                  disabled={isAddingAccount || editingAccount !== null}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Account
                </Button>
              </CardTitle>
              <CardDescription>Configure your Apex funded trading accounts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Existing Accounts */}
              {apexAccounts.map((account) => (
                <div
                  key={account.id}
                  className="border rounded-lg p-4 space-y-2 bg-muted/30"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold">{account.account_name}</h4>
                      <p className="text-sm text-muted-foreground">
                        ${(account.account_size_usd / 1000).toFixed(0)}K Account
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingAccount(account)}
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleTestAccount(account.id)}
                        disabled={account.status === 'testing'}
                      >
                        <TestTube className="h-3 w-3 mr-1" />
                        Test
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Trailing threshold:</span>{' '}
                      ${account.trailing_threshold_usd.toLocaleString()}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Max daily loss:</span>{' '}
                      ${account.max_daily_loss_usd.toLocaleString()}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Max contracts:</span>{' '}
                      {account.max_contracts}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Consistency rule:</span>{' '}
                      {account.consistency_pct}%
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-sm">
                    <CircleDot
                      className={`h-3 w-3 ${
                        account.status === 'connected'
                          ? 'text-green-500'
                          : account.status === 'testing'
                            ? 'text-yellow-500'
                            : 'text-red-500'
                      }`}
                    />
                    <span className="text-muted-foreground">Status:</span>
                    <span className="font-medium">{account.status}</span>
                  </div>
                </div>
              ))}

              {/* Add/Edit Form */}
              {(isAddingAccount || editingAccount) && (
                <div className="border rounded-lg p-4 space-y-4 bg-background">
                  <h4 className="font-semibold">
                    {editingAccount ? 'Edit Account' : 'New Account'}
                  </h4>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="account_name">Account Name</Label>
                      <Input
                        id="account_name"
                        value={accountToEdit.account_name || ''}
                        onChange={(e) =>
                          editingAccount
                            ? setEditingAccount({ ...editingAccount, account_name: e.target.value })
                            : setNewAccount({ ...newAccount, account_name: e.target.value })
                        }
                        placeholder="NQ Futures Account"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="account_size">Account Size</Label>
                      <Select
                        value={accountToEdit.account_size_usd?.toString()}
                        onValueChange={handleAccountSizeChange}
                      >
                        <SelectTrigger id="account_size">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="25000">$25K</SelectItem>
                          <SelectItem value="50000">$50K</SelectItem>
                          <SelectItem value="100000">$100K</SelectItem>
                          <SelectItem value="250000">$250K</SelectItem>
                          <SelectItem value="300000">$300K</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="trailing_threshold">Trailing Threshold (auto-filled)</Label>
                      <Input
                        id="trailing_threshold"
                        type="number"
                        value={accountToEdit.trailing_threshold_usd || ''}
                        onChange={(e) =>
                          editingAccount
                            ? setEditingAccount({
                                ...editingAccount,
                                trailing_threshold_usd: parseInt(e.target.value),
                              })
                            : setNewAccount({
                                ...newAccount,
                                trailing_threshold_usd: parseInt(e.target.value),
                              })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="max_daily_loss">Max Daily Loss</Label>
                      <Input
                        id="max_daily_loss"
                        type="number"
                        value={accountToEdit.max_daily_loss_usd || ''}
                        onChange={(e) =>
                          editingAccount
                            ? setEditingAccount({
                                ...editingAccount,
                                max_daily_loss_usd: parseInt(e.target.value),
                              })
                            : setNewAccount({
                                ...newAccount,
                                max_daily_loss_usd: parseInt(e.target.value),
                              })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="max_contracts">Max Contracts (auto-filled)</Label>
                      <Input
                        id="max_contracts"
                        type="number"
                        value={accountToEdit.max_contracts || ''}
                        onChange={(e) =>
                          editingAccount
                            ? setEditingAccount({
                                ...editingAccount,
                                max_contracts: parseInt(e.target.value),
                              })
                            : setNewAccount({
                                ...newAccount,
                                max_contracts: parseInt(e.target.value),
                              })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="consistency_pct">Consistency %</Label>
                      <Input
                        id="consistency_pct"
                        type="number"
                        value={accountToEdit.consistency_pct || 30}
                        onChange={(e) =>
                          editingAccount
                            ? setEditingAccount({
                                ...editingAccount,
                                consistency_pct: parseInt(e.target.value),
                              })
                            : setNewAccount({
                                ...newAccount,
                                consistency_pct: parseInt(e.target.value),
                              })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="news_blackout">News Blackout (minutes)</Label>
                      <Input
                        id="news_blackout"
                        type="number"
                        value={accountToEdit.news_blackout_minutes || 5}
                        onChange={(e) =>
                          editingAccount
                            ? setEditingAccount({
                                ...editingAccount,
                                news_blackout_minutes: parseInt(e.target.value),
                              })
                            : setNewAccount({
                                ...newAccount,
                                news_blackout_minutes: parseInt(e.target.value),
                              })
                        }
                      />
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button onClick={handleSaveAccount}>Save</Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setIsAddingAccount(false);
                        setEditingAccount(null);
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Section 2: Credentials */}
        <TabsContent value="credentials" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                API Credentials
              </CardTitle>
              <CardDescription>
                Manage secure credentials. Values are never displayed, only status.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Rithmic */}
              <div className="space-y-3">
                <h4 className="font-semibold">Rithmic</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-32 text-sm text-muted-foreground">Username:</div>
                      <div className="font-mono text-sm">●●●●●●●●●●</div>
                      {credentials.rithmic_username === 'configured' ? (
                        <div className="flex items-center gap-1 text-sm text-green-600">
                          <Check className="h-3 w-3" />
                          configured
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-sm text-red-600">
                          <X className="h-3 w-3" />
                          not configured
                        </div>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setCredentialModal({ open: true, key: 'rithmic_username', value: '' })
                      }
                    >
                      Update
                    </Button>
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-32 text-sm text-muted-foreground">Password:</div>
                      <div className="font-mono text-sm">●●●●●●●●●●</div>
                      {credentials.rithmic_password === 'configured' ? (
                        <div className="flex items-center gap-1 text-sm text-green-600">
                          <Check className="h-3 w-3" />
                          configured
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-sm text-red-600">
                          <X className="h-3 w-3" />
                          not configured
                        </div>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setCredentialModal({ open: true, key: 'rithmic_password', value: '' })
                      }
                    >
                      Update
                    </Button>
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-32 text-sm text-muted-foreground">Server:</div>
                      <div className="text-sm font-medium">{credentials.rithmic_server}</div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setCredentialModal({ open: true, key: 'rithmic_server', value: credentials.rithmic_server })
                      }
                    >
                      Update
                    </Button>
                  </div>
                </div>
              </div>

              {/* SendGrid */}
              <div className="space-y-3">
                <h4 className="font-semibold">SendGrid API Key</h4>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-32 text-sm text-muted-foreground">Key:</div>
                    <div className="font-mono text-sm">●●●●●●●●●●●●●●●</div>
                    {credentials.sendgrid_api_key === 'configured' ? (
                      <div className="flex items-center gap-1 text-sm text-green-600">
                        <Check className="h-3 w-3" />
                        configured
                      </div>
                    ) : (
                      <div className="flex items-center gap-1 text-sm text-red-600">
                        <X className="h-3 w-3" />
                        not configured
                      </div>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      setCredentialModal({ open: true, key: 'sendgrid_api_key', value: '' })
                    }
                  >
                    Update
                  </Button>
                </div>
              </div>

              {/* Telegram */}
              <div className="space-y-3">
                <h4 className="font-semibold">Telegram Bot</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-32 text-sm text-muted-foreground">Bot Token:</div>
                      <div className="font-mono text-sm">●●●●●●●●●</div>
                      {credentials.telegram_bot_token === 'configured' ? (
                        <div className="flex items-center gap-1 text-sm text-green-600">
                          <Check className="h-3 w-3" />
                          configured
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-sm text-red-600">
                          <X className="h-3 w-3" />
                          not configured
                        </div>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setCredentialModal({ open: true, key: 'telegram_bot_token', value: '' })
                      }
                    >
                      Update
                    </Button>
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-32 text-sm text-muted-foreground">Chat ID:</div>
                      <div className="text-sm font-medium">
                        {credentials.telegram_chat_id || '(not set)'}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setCredentialModal({
                          open: true,
                          key: 'telegram_chat_id',
                          value: credentials.telegram_chat_id,
                        })
                      }
                    >
                      Update
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Section 3: Trading Schedules */}
        <TabsContent value="schedules" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Trading Schedules
              </CardTitle>
              <CardDescription>Define when the bot can place trades</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <h4 className="font-semibold">Allowed Trading Sessions</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">NY AM Session</div>
                      <div className="text-sm text-muted-foreground">9:30 AM - 12:00 PM ET</div>
                    </div>
                    <Switch
                      checked={schedules.ny_am_session}
                      onCheckedChange={(checked) =>
                        setSchedules({ ...schedules, ny_am_session: checked })
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">NY PM Session</div>
                      <div className="text-sm text-muted-foreground">1:00 PM - 3:45 PM ET</div>
                    </div>
                    <Switch
                      checked={schedules.ny_pm_session}
                      onCheckedChange={(checked) =>
                        setSchedules({ ...schedules, ny_pm_session: checked })
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">London Session</div>
                      <div className="text-sm text-muted-foreground">3:00 AM - 6:00 AM ET</div>
                    </div>
                    <Switch
                      checked={schedules.london_session}
                      onCheckedChange={(checked) =>
                        setSchedules({ ...schedules, london_session: checked })
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">Asia Session</div>
                      <div className="text-sm text-muted-foreground">8:00 PM - 11:00 PM ET</div>
                    </div>
                    <Switch
                      checked={schedules.asia_session}
                      onCheckedChange={(checked) =>
                        setSchedules({ ...schedules, asia_session: checked })
                      }
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-semibold">Always Blocked</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 p-3 border rounded-lg bg-muted/50">
                    <Check className="h-4 w-4 text-green-600" />
                    <div>
                      <div className="font-medium">4:00 PM - 5:00 PM ET (Apex maintenance)</div>
                      <div className="text-sm text-muted-foreground">Cannot be disabled</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 p-3 border rounded-lg bg-muted/50">
                    <Check className="h-4 w-4 text-green-600" />
                    <div>
                      <div className="font-medium">30min before FOMC/NFP/CPI</div>
                      <div className="text-sm text-muted-foreground">Economic event protection</div>
                    </div>
                  </div>
                </div>
              </div>

              <Button onClick={handleSaveSchedules}>Save Schedules</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Section 4: Alert Notifications */}
        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  Alert Notifications
                </span>
                <Button size="sm" onClick={handleTestAlert}>
                  <TestTube className="h-4 w-4 mr-2" />
                  Test Alert
                </Button>
              </CardTitle>
              <CardDescription>Configure notification channels for each event type</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-semibold">Event</th>
                      <th className="text-center py-3 px-4 font-semibold">Telegram</th>
                      <th className="text-center py-3 px-4 font-semibold">Email</th>
                      <th className="text-center py-3 px-4 font-semibold">In-app</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(notifications).map(([event, channels]) => (
                      <tr key={event} className="border-b">
                        <td className="py-3 px-4">
                          <div className="font-medium">
                            {event.split('_').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                          </div>
                        </td>
                        <td className="text-center py-3 px-4">
                          <Switch
                            checked={channels.telegram}
                            onCheckedChange={(checked) =>
                              setNotifications({
                                ...notifications,
                                [event]: { ...channels, telegram: checked },
                              })
                            }
                          />
                        </td>
                        <td className="text-center py-3 px-4">
                          <Switch
                            checked={channels.email}
                            onCheckedChange={(checked) =>
                              setNotifications({
                                ...notifications,
                                [event]: { ...channels, email: checked },
                              })
                            }
                          />
                        </td>
                        <td className="text-center py-3 px-4">
                          <Switch
                            checked={channels.in_app}
                            onCheckedChange={(checked) =>
                              setNotifications({
                                ...notifications,
                                [event]: { ...channels, in_app: checked },
                              })
                            }
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-6">
                <Button onClick={handleSaveNotifications}>Save Notifications</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Credential Update Modal */}
      <Dialog open={credentialModal.open} onOpenChange={(open) => !open && setCredentialModal({ open: false, key: '', value: '' })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Credential</DialogTitle>
            <DialogDescription>
              Enter the new value for{' '}
              {credentialModal.key.split('_').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="credential_value">New Value</Label>
              <Input
                id="credential_value"
                type={credentialModal.key.includes('password') || credentialModal.key.includes('token') || credentialModal.key.includes('key') ? 'password' : 'text'}
                value={credentialModal.value}
                onChange={(e) =>
                  setCredentialModal({ ...credentialModal, value: e.target.value })
                }
                placeholder="Enter new value"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCredentialModal({ open: false, key: '', value: '' })}>
              Cancel
            </Button>
            <Button onClick={handleUpdateCredential}>Update</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Settings;
