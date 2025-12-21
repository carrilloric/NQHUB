/**
 * AI Assistant Panel - Sidebar Layout (for Data Module, Statistical Analysis, etc.)
 * Replaces ChatWorkspaceAside with assistant in right sidebar
 */
import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { SendHorizonal, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { assistantApi } from './services/assistantApi';
import type { Message } from './types';
import { useToast } from '@/components/ui/use-toast';

export const AssistantPanelSidebar: React.FC = () => {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

      if (!currentConversationId) {
        setCurrentConversationId(response.conversation_id);
      }

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

  return (
    <aside className="w-80 border-l border-border bg-card/50 flex flex-col overflow-hidden sticky top-16 min-h-[calc(100vh-4rem)]">
      {/* Messages Area */}
      <div className="flex-1 overflow-auto p-4 flex flex-col justify-end">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground text-sm py-4">
            <p>Pregunta sobre datos o patrones</p>
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex",
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    "max-w-[90%] rounded-lg px-3 py-2",
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground'
                  )}
                >
                  <p className="text-xs whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input Area */}
        <div className="mt-4">
          <div className="rounded-2xl border border-input bg-card shadow-lg">
            <div className="relative">
              <textarea
                rows={3}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Pregúntame..."
                disabled={isLoading}
                className={cn(
                  "w-full resize-none bg-transparent outline-none px-4 py-4 text-sm",
                  "placeholder:text-muted-foreground"
                )}
              />
            </div>
            <div className="flex items-center justify-between px-3 pb-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setMessages([]);
                  setCurrentConversationId(undefined);
                }}
                className="text-xs"
              >
                New Chat
              </Button>
              <Button onClick={handleSend} disabled={!input.trim() || isLoading} size="sm">
                {isLoading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <>
                    <SendHorizonal className="h-3 w-3 mr-1" />
                    Send
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border text-xs text-muted-foreground text-center">
        Powered by NQHUB Assistant
      </div>
    </aside>
  );
};
