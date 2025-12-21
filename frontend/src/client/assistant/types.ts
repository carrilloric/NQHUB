/**
 * TypeScript types for AI Assistant
 */

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: number;
  title?: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ConversationListItem {
  id: string;
  user_id: number;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  user_message: Message;
  assistant_message: Message;
  metadata?: Record<string, any>;
}

export interface SystemEvent {
  id: string;
  event_type: string;
  event_data: Record<string, any>;
  notified: boolean;
  created_at: string;
}

export interface ETLStatus {
  total_jobs: number;
  running: number;
  completed: number;
  failed: number;
  recent_jobs: any[];
}

export interface PatternStatus {
  total_fvgs: number;
  total_lps: number;
  total_obs: number;
  recent_detections: any[];
}

export interface DatabaseStats {
  total_candles: number;
  total_ticks: number;
  active_contracts: number;
  coverage_summary: Record<string, number>;
}

export interface SystemHealth {
  api_status: string;
  database_status: string;
  redis_status: string;
  workers_active: number;
  workers_total: number;
  memory_usage?: {
    total_gb: number;
    used_gb: number;
    percent: number;
  };
  cpu_percent?: number;
  disk_usage?: {
    total_gb: number;
    used_gb: number;
    percent: number;
  };
}

// Vanna.AI types
export interface VannaCollection {
  name: string;
  count: number;
  metadata?: Record<string, any>;
}

export interface VannaCategoryBreakdown {
  fvg: number;
  liquidity_pools: number;
  order_blocks: number;
  etl: number;
  candles: number;
  other: number;
}

export interface VannaStats {
  status: 'active' | 'unavailable' | 'error';
  message?: string;
  chroma_path?: string;
  collections?: VannaCollection[];
  total_documents: number;
  total_ddl: number;
  total_sql_examples: number;
  total_documentation: number;
  breakdown?: VannaCategoryBreakdown;
}

export interface VannaQuery {
  id: string;
  content: string;
  metadata?: Record<string, any>;
}

export interface VannaSimilarQuery {
  content: string;
  distance: number;
  metadata?: Record<string, any>;
}

export interface VannaSimilarRequest {
  question: string;
  limit?: number;
}
