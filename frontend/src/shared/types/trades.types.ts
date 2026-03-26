/**
 * Trade History Types
 */

export interface Trade {
  id: string;
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  commission: number;
  executed_at: string;
  pnl?: number;
  pnl_ticks?: number;
  position_id?: string;
  bot_id?: string;
  strategy_id?: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  realized_pnl: number;
  opened_at: string;
  closed_at?: string;
  status: 'open' | 'closed';
}

export interface TradePerformance {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  gross_pnl: number;
  net_pnl: number;
  commissions: number;
  average_win: number;
  average_loss: number;
  profit_factor: number;
  max_win: number;
  max_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
  daily_stats?: DailyStats[];
}

export interface DailyStats {
  date: string;
  trades: number;
  gross_pnl: number;
  net_pnl: number;
  win_rate: number;
}