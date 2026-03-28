/**
 * Order Management Types
 */

export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  status: 'pending' | 'submitted' | 'filled' | 'partial' | 'cancelled' | 'rejected';
  quantity: number;
  price?: number;
  stop_price?: number;
  filled_quantity: number;
  average_fill_price?: number;
  created_at: string;
  submitted_at?: string;
  filled_at?: string;
  cancelled_at?: string;
  source: 'manual' | 'bot' | 'strategy';
  bot_id?: string;
  strategy_id?: string;
  error_message?: string;
}

export interface SubmitOrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price?: number;
  stop_price?: number;
  time_in_force?: 'DAY' | 'GTC' | 'IOC' | 'FOK';
}