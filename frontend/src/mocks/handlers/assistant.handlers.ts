import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

interface ChatRequest {
  messages: Array<{ role: 'user' | 'assistant'; content: string }>;
  page_context?: string;
}

// Simulated responses based on page context
const getContextualResponse = (pageContext: string, userMessage: string): string => {
  const lowerMessage = userMessage.toLowerCase();

  // Context-specific responses
  if (pageContext === 'live_dashboard') {
    if (lowerMessage.includes('bias') || lowerMessage.includes('mercado')) {
      return 'El bias actual en **NQ 5min** es **bearish**. El POC está en **18,285** y el precio está operando por debajo de este nivel. La estructura muestra **Lower Highs** y **Lower Lows**.';
    }
    return 'En el Live Dashboard puedo ayudarte a analizar el mercado en tiempo real. ¿Quieres saber el bias actual, revisar niveles clave o analizar el orderflow?';
  }

  if (pageContext === 'backtesting') {
    return 'En Backtesting puedo ayudarte a evaluar estrategias históricas. ¿Quieres revisar los resultados de un backtest existente o crear uno nuevo?';
  }

  if (pageContext === 'patterns') {
    if (lowerMessage.includes('fvg') || lowerMessage.includes('gap')) {
      return 'Encontré **3 Fair Value Gaps** sin mitigar en el gráfico actual:\n- **FVG Bullish** en 18,250-18,265 (formado 09:45 ET)\n- **FVG Bearish** en 18,310-18,325 (formado 11:20 ET)\n- **FVG Bearish** en 18,290-18,300 (formado 13:15 ET)';
    }
    return 'Puedo ayudarte a detectar patrones ICT como Fair Value Gaps, Liquidity Pools y Order Blocks. ¿Qué tipo de patrón te interesa analizar?';
  }

  if (pageContext === 'data') {
    return 'Puedo ayudarte con la gestión de datos: consultar cobertura, verificar calidad de datos, o analizar estadísticas de la base de datos.';
  }

  // Generic response
  return 'Soy el asistente de NQHUB. Puedo ayudarte a analizar el mercado, revisar patrones ICT, verificar backtests, consultar datos y más. ¿En qué puedo asistirte?';
};

// Simulated tool usage based on query type
const getToolsUsed = (userMessage: string): string[] => {
  const lowerMessage = userMessage.toLowerCase();
  const tools: string[] = [];

  if (lowerMessage.includes('bias') || lowerMessage.includes('mercado') || lowerMessage.includes('market')) {
    tools.push('query_market_snapshot');
  }
  if (lowerMessage.includes('fvg') || lowerMessage.includes('gap') || lowerMessage.includes('pattern')) {
    tools.push('query_detected_patterns');
  }
  if (lowerMessage.includes('backtest') || lowerMessage.includes('resultado')) {
    tools.push('query_backtests');
  }
  if (lowerMessage.includes('data') || lowerMessage.includes('cobertura') || lowerMessage.includes('coverage')) {
    tools.push('query_data_coverage');
  }
  if (lowerMessage.includes('sql') || lowerMessage.includes('query')) {
    tools.push('run_sql');
  }

  return tools;
};

export const assistantHandlers = [
  http.post(`${API_BASE}/assistant/chat`, async ({ request }) => {
    const body = (await request.json()) as ChatRequest;

    // Get last user message
    const lastMessage = body.messages[body.messages.length - 1];
    const pageContext = body.page_context || 'general';

    // Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    const message = getContextualResponse(pageContext, lastMessage.content);
    const tools_used = getToolsUsed(lastMessage.content);

    return HttpResponse.json({
      message,
      tools_used: tools_used.length > 0 ? tools_used : undefined,
      usage: {
        input_tokens: Math.floor(Math.random() * 200) + 350,
        output_tokens: Math.floor(Math.random() * 100) + 50,
      },
    });
  }),

  http.get(`${API_BASE}/assistant/conversations`, () => HttpResponse.json([])),
];