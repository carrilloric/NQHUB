/**
 * Backtesting Types
 */

export interface BacktestStrategy {
  id: string;
  name: string;
  type: 'rule_based' | 'ai_powered';
  parameters: Record<string, any>;
  entry_rules?: string[];
  exit_rules?: string[];
  risk_management?: RiskParams;
}

export interface RiskParams {
  stop_loss_ticks: number;
  take_profit_ticks: number;
  max_position_size: number;
  max_daily_loss: number;
}

export interface BacktestRun {
  id: string;
  strategy_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  start_date: string;
  end_date: string;
  symbol: string;
  timeframe: string;
  created_at: string;
  completed_at?: string;
  results?: BacktestResults;
  error?: string;
}

export interface BacktestResults {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_pnl: number;
  average_win: number;
  average_loss: number;
  trades: BacktestTrade[];
  equity_curve: Array<{
    timestamp: string;
    equity: number;
  }>;
}

export interface BacktestTrade {
  id: string;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  side: 'long' | 'short';
  quantity: number;
  pnl: number;
  pnl_ticks: number;
  entry_reason: string;
  exit_reason: string;
}