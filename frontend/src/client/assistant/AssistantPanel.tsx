/**
 * AI Assistant Panel - Main component
 *
 * Replaces the old LLMPanel with full functionality
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useUI } from '@/state/app';
import { Button } from '@/components/ui/button';
import { SendHorizonal, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { assistantApi } from './services/assistantApi';
import type { Message, SystemEvent } from './types';
import { useToast } from '@/components/ui/use-toast';

export const AssistantPanel: React.FC = () => {
  const ui = useUI();
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Polling for system events (every 15s)
  useEffect(() => {
    if (!ui.llmPanelOpen) return;

    const pollEvents = async () => {
      try {
        const events = await assistantApi.getEvents();
        if (events.length > 0) {
          // Show toast notifications
          events.forEach((event: SystemEvent) => {
            toast({
              title: formatEventTitle(event.event_type),
              description: formatEventDescription(event),
            });
          });

          // Mark as read
          const eventIds = events.map(e => e.id);
          await assistantApi.markEventsRead(eventIds);
        }
      } catch (error) {
        console.error('Failed to poll events:', error);
      }
    };

    // Initial poll
    pollEvents();

    // Setup interval
    const interval = setInterval(pollEvents, 15000); // 15 seconds

    return () => clearInterval(interval);
  }, [ui.llmPanelOpen, toast]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message optimistically
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversationId || '',
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await assistantApi.chat({
        message: userMessage,
        conversation_id: currentConversationId,
      });

      // Update conversation ID
      if (!currentConversationId) {
        setCurrentConversationId(response.conversation_id);
      }

      // Replace temp message with real ones
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== tempUserMsg.id);
        return [...filtered, response.user_message, response.assistant_message];
      });

    } catch (error: any) {
      console.error('Chat error:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to send message',
        variant: 'destructive',
      });

      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Panel resize handler
  const startY = useRef<number | null>(null);
  const startH = useRef<number>(ui.llmPanelHeight);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    startY.current = e.clientY;
    startH.current = ui.llmPanelHeight;

    const onMove = (ev: MouseEvent) => {
      if (startY.current == null) return;
      const delta = startY.current - ev.clientY;
      const next = Math.min(Math.max(200, startH.current + delta), window.innerHeight - 120);
      ui.setLlmPanelHeight(next);
    };

    const onUp = () => {
      startY.current = null;
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }, [ui]);

  if (!ui.llmPanelOpen) return null;

  return (
    <div className="fixed left-0 right-0 bottom-0 z-30" style={{ height: ui.llmPanelHeight }}>
      {/* Resize handle */}
      <div className="h-3 cursor-ns-resize bg-border/50 hover:bg-border" onMouseDown={onMouseDown} />

      <div className="h-[calc(100%-12px)] bg-card border-t border-border/60 flex flex-col">
        {/* Header */}
        <div className="border-b border-border/60 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm font-semibold">AI Assistant</span>
            <span className="text-xs text-muted-foreground">Powered by Claude</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setMessages([]);
              setCurrentConversationId(undefined);
            }}
          >
            New Chat
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p className="text-sm">Ask me anything about your data, patterns, or system status.</p>
              <p className="text-xs mt-2">I can query the database, check ETL jobs, and more!</p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex gap-3",
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] rounded-lg px-4 py-2",
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                )}
              >
                <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                {msg.metadata?.sql && (
                  <details className="mt-2 text-xs opacity-70">
                    <summary className="cursor-pointer">SQL Query</summary>
                    <pre className="mt-1 p-2 bg-black/20 rounded overflow-x-auto">
                      <code>{msg.metadata.sql}</code>
                    </pre>
                  </details>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border/60 p-3 flex items-end gap-2">
          <textarea
            className={cn(
              "flex-1 min-h-[44px] max-h-32 rounded-md bg-background px-3 py-2 text-sm outline-none border border-input focus:ring-2 focus:ring-ring resize-none"
            )}
            placeholder="Ask me anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            rows={1}
          />
          <Button onClick={handleSend} disabled={!input.trim() || isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <SendHorizonal className="h-4 w-4 mr-2" />
                Send
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

// Helper functions
function formatEventTitle(eventType: string): string {
  const titles: Record<string, string> = {
    etl_complete: '✅ ETL Job Completed',
    etl_failed: '❌ ETL Job Failed',
    pattern_detected: '🎯 New Pattern Detected',
    system_alert: '⚠️ System Alert',
    database_stats: '📊 Database Update',
  };
  return titles[eventType] || '📢 System Notification';
}

function formatEventDescription(event: SystemEvent): string {
  const { event_type, event_data } = event;

  if (event_type === 'etl_complete') {
    return `Job #${event_data.job_id || 'N/A'} completed. Processed ${event_data.rows_processed || 0} rows.`;
  }

  if (event_type === 'pattern_detected') {
    return `New ${event_data.pattern_type || 'pattern'} detected at ${event_data.level || 'N/A'}`;
  }

  return event_data.message || 'System notification';
}
