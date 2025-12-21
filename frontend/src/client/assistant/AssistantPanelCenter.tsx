/**
 * AI Assistant Panel - Center Layout (for Dashboard)
 * Replaces ChatWorkspace with assistant in center of page
 */
import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { SendHorizonal, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { assistantApi } from './services/assistantApi';
import type { Message } from './types';
import { useToast } from '@/components/ui/use-toast';

export const AssistantPanelCenter: React.FC<{ title?: string }> = ({ title }) => {
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
    <section className="relative flex min-h-[calc(100vh-4rem)] w-full flex-col items-center justify-start overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(23,211,218,0.12),_transparent)] pb-20 pt-10">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgba(11,17,29,0.95),rgba(6,10,18,0.92))]" aria-hidden />
      <div className="relative z-10 mx-auto flex w-full max-w-5xl flex-col gap-10 px-4 md:px-8">
        {/* Header */}
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-5xl font-black uppercase tracking-[0.42em] text-foreground/95">
              <span className="text-secondary">NQ</span>HUB
            </div>
            {title && (
              <p className="mt-3 text-xs font-semibold uppercase tracking-[0.32em] text-muted-foreground/70">
                {title}
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3 text-right text-xs uppercase tracking-[0.28em] text-muted-foreground/70">
            <StatBlock label="Open" value="15,182" trend="bullish" />
            <StatBlock label="High" value="15,342" trend="bullish" />
            <StatBlock label="Low" value="15,021" trend="bearish" />
            <StatBlock label="Volume" value="3.2M" />
          </div>
        </div>

        {/* Chat Container */}
        <div className="rounded-3xl border border-border/40 bg-gradient-to-br from-[#131d2f] via-[#0c1523] to-[#09101b] shadow-[0_24px_48px_rgba(0,0,0,0.55)]">
          {/* Messages Area */}
          <div className="min-h-[300px] max-h-[400px] overflow-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <p className="text-base">Pregúntame sobre tus datos, patrones o estado del sistema</p>
                <p className="text-sm mt-2">Puedo consultar la base de datos, verificar trabajos ETL y más</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex",
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] rounded-lg px-4 py-2",
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-foreground'
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="relative border-t border-border/40">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              disabled={isLoading}
              className={cn(
                "w-full resize-none bg-transparent px-6 py-5 text-base text-foreground/90 outline-none",
                "placeholder:text-muted-foreground"
              )}
            />
            <div className="absolute right-4 bottom-4">
              <Button onClick={handleSend} disabled={!input.trim() || isLoading} className="rounded-full">
                {isLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    <SendHorizonal className="h-5 w-5 mr-2" />
                    Send
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Quick Access Buttons */}
        <div className="flex gap-3 justify-center">
          <QuickAccessButton>DATA MODULE</QuickAccessButton>
          <QuickAccessButton>NQ STATS</QuickAccessButton>
          <QuickAccessButton>BACKTESTING</QuickAccessButton>
          <QuickAccessButton>TRADECADEMY</QuickAccessButton>
        </div>
      </div>
    </section>
  );
};

const StatBlock: React.FC<{ label: string; value: string; trend?: 'bullish' | 'bearish' }> = ({ label, value, trend }) => (
  <div>
    <div className="text-[10px] font-medium">{label}</div>
    <div className={cn("text-sm font-semibold tabular-nums", trend === 'bullish' ? 'text-bullish' : trend === 'bearish' ? 'text-bearish' : 'text-foreground')}>
      {value}
    </div>
  </div>
);

const QuickAccessButton: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <button className="px-6 py-3 text-xs font-semibold uppercase tracking-[0.28em] border border-border/40 rounded-lg hover:bg-accent/50 transition-colors">
    {children}
  </button>
);
