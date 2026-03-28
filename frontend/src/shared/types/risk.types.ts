/**
 * Risk Management Types
 */

export interface RiskStatus {
  account_equity: number;
  cash_balance: number;
  open_positions: number;
  total_exposure: number;
  daily_pnl: number;
  daily_loss_limit: number;
  max_drawdown: number;
  current_drawdown: number;
  risk_score: number;
  alerts: RiskAlert[];
}

export interface RiskAlert {
  id: string;
  level: 'info' | 'warning' | 'critical';
  type: 'position_size' | 'daily_loss' | 'drawdown' | 'correlation' | 'volatility';
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface RiskConfig {
  max_position_size: number;
  max_daily_loss: number;
  max_drawdown: number;
  max_correlation: number;
  position_sizing_method: 'fixed' | 'percent' | 'kelly';
  stop_loss_required: boolean;
  auto_liquidate: boolean;
  alert_thresholds: {
    drawdown_warning: number;
    daily_loss_warning: number;
    position_size_warning: number;
  };
}

export interface EmergencyStopRequest {
  reason: string;
  close_all_positions: boolean;
  cancel_all_orders: boolean;
  disable_trading: boolean;
}