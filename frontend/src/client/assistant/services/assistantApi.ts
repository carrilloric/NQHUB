/**
 * API client for AI Assistant endpoints
 */
import axios from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  ConversationListItem,
  SystemEvent,
  ETLStatus,
  PatternStatus,
  DatabaseStats,
  SystemHealth,
} from '../types';

// Create Axios instance specifically for assistant endpoints
const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add Bearer token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('nqhub_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const assistantApi = {
  // Chat
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await client.post('/assistant/chat', request);
    return data;
  },

  // Conversations
  async getConversations(): Promise<ConversationListItem[]> {
    const { data } = await client.get('/assistant/conversations');
    return data;
  },

  async getConversation(id: string): Promise<Conversation> {
    const { data } = await client.get(`/assistant/conversations/${id}`);
    return data;
  },

  async deleteConversation(id: string): Promise<void> {
    await client.delete(`/assistant/conversations/${id}`);
  },

  // System Events (for polling)
  async getEvents(): Promise<SystemEvent[]> {
    const { data } = await client.get('/assistant/events');
    return data;
  },

  async markEventsRead(eventIds: string[]): Promise<void> {
    await client.post('/assistant/events/mark-read', { event_ids: eventIds });
  },

  // Status endpoints
  async getETLStatus(): Promise<ETLStatus> {
    const { data } = await client.get('/assistant/status/etl');
    return data;
  },

  async getPatternStatus(): Promise<PatternStatus> {
    const { data } = await client.get('/assistant/status/patterns');
    return data;
  },

  async getDatabaseStats(): Promise<DatabaseStats> {
    const { data} = await client.get('/assistant/status/database');
    return data;
  },

  async getSystemHealth(): Promise<SystemHealth> {
    const { data } = await client.get('/assistant/status/system');
    return data;
  },

  // Feedback
  async submitFeedback(messageId: string, rating: number, comment?: string): Promise<void> {
    await client.post('/assistant/feedback', {
      message_id: messageId,
      rating,
      comment,
    });
  },

  // Vanna.AI endpoints
  async getVannaStats(): Promise<import('../types').VannaStats> {
    const { data } = await client.get('/vanna/stats');
    return data;
  },

  async getVannaQueries(limit = 50): Promise<import('../types').VannaQuery[]> {
    const { data } = await client.get(`/vanna/queries?limit=${limit}`);
    return data;
  },

  async findSimilarQueries(question: string, limit = 5): Promise<import('../types').VannaSimilarQuery[]> {
    const { data } = await client.post('/vanna/similar', { question, limit });
    return data;
  },

  async exportVannaData(): Promise<any> {
    const { data } = await client.get('/vanna/export');
    return data;
  },
};
