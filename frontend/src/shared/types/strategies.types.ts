/**
 * Strategy Management Types
 */

export interface Strategy {
  id: string;
  name: string;
  description: string;
  type: 'rule_based' | 'ml_based' | 'hybrid';
  status: 'draft' | 'testing' | 'approved' | 'live' | 'deprecated';
  version: string;
  author_id: string;
  created_at: string;
  updated_at: string;
  config: StrategyConfig;
  backtest_results?: BacktestSummary;
  approval_status?: ApprovalStatus;
}

export interface StrategyConfig {
  indicators: string[];
  entry_rules: EntryRule[];
  exit_rules: ExitRule[];
  risk_management: RiskManagement;
  timeframes: string[];
  symbols: string[];
}

export interface EntryRule {
  id: string;
  type: 'indicator_cross' | 'price_action' | 'pattern' | 'ml_signal';
  condition: string;
  parameters: Record<string, any>;
}

export interface ExitRule {
  id: string;
  type: 'stop_loss' | 'take_profit' | 'trailing_stop' | 'indicator' | 'time';
  condition: string;
  parameters: Record<string, any>;
}

export interface RiskManagement {
  position_sizing: 'fixed' | 'percent' | 'volatility_based';
  max_position_size: number;
  stop_loss_ticks: number;
  take_profit_ticks?: number;
  max_daily_trades: number;
}

export interface BacktestSummary {
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  annual_return: number;
}

export interface ApprovalStatus {
  status: 'pending' | 'approved' | 'rejected';
  reviewer_id?: string;
  reviewed_at?: string;
  comments?: string;
}