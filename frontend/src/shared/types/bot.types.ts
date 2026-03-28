/**
 * Trading Bot Types
 */

export interface TradingBot {
  id: string;
  name: string;
  strategy_id: string;
  status: 'idle' | 'running' | 'paused' | 'error';
  mode: 'paper' | 'live';
  created_at: string;
  started_at?: string;
  config: BotConfig;
  performance?: BotPerformance;
}

export interface BotConfig {
  symbol: string;
  timeframe: string;
  risk_per_trade: number;
  max_positions: number;
  daily_loss_limit: number;
  trading_hours?: {
    start: string;
    end: string;
  };
  auto_restart: boolean;
}

export interface BotPerformance {
  total_trades: number;
  open_positions: number;
  daily_pnl: number;
  total_pnl: number;
  win_rate: number;
  average_win: number;
  average_loss: number;
  last_trade?: string;
}

export interface BotCommand {
  bot_id: string;
  action: 'start' | 'stop' | 'pause' | 'resume';
  params?: Record<string, any>;
}