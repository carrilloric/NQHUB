/**
 * AI Assistant Types
 */

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  model?: string;
  tokens_used?: number;
  processing_time_ms?: number;
  sources?: string[];
  confidence?: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
  context?: ConversationContext;
}

export interface ConversationContext {
  active_chart?: string;
  selected_timeframe?: string;
  selected_symbol?: string;
  detected_patterns?: string[];
  active_strategy?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  context?: ConversationContext;
  include_charts?: boolean;
  include_patterns?: boolean;
}

export interface ChatResponse {
  message: ChatMessage;
  suggestions?: string[];
  actions?: AssistantAction[];
}

export interface AssistantAction {
  type: 'create_chart' | 'run_backtest' | 'analyze_pattern' | 'generate_strategy';
  label: string;
  params: Record<string, any>;
}