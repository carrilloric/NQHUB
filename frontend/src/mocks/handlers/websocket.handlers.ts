/**
 * MSW WebSocket Handlers for Live Trading
 *
 * Based on contract-005-websocket.yaml
 * Implements WebSocket mock for frontend development
 */

import { ws } from 'msw';

// WebSocket endpoint
const liveWs = ws.link('ws://localhost:8002/ws/live');

// Helper to generate mock data
const generateMockTick = () => ({
  channel: 'price',
  event: 'tick',
  data: {
    symbol: 'NQH25',
    price: 20150.25 + Math.random() * 10 - 5,
    size: Math.floor(Math.random() * 10) + 1,
    side: Math.random() > 0.5 ? 'BUY' : 'SELL',
  },
  timestamp: new Date().toISOString(),
  bot_id: '550e8400-e29b-41d4-a716-446655440000',
});

const generateMockBarUpdate = (timeframe: string) => ({
  channel: 'price',
  event: 'barUpdate',
  data: {
    symbol: 'NQH25',
    timeframe,
    open: 20150,
    high: 20155,
    low: 20148,
    close: 20152 + Math.random() * 2,
    volume: Math.floor(Math.random() * 1000) + 100,
  },
  timestamp: new Date().toISOString(),
  bot_id: '550e8400-e29b-41d4-a716-446655440000',
});

const generateMockPortfolioUpdate = () => {
  // Generate equity curve data (last 30 data points)
  const equityCurve = [];
  const drawdownSeries = [];
  const baseEquity = 25000;

  for (let i = 0; i < 30; i++) {
    const trend = i * 20;
    const noise = Math.sin(i * 0.5) * 200 + Math.random() * 100 - 50;
    const equity = baseEquity + trend + noise;
    const drawdown = Math.max(0, baseEquity + i * 30 - equity);

    equityCurve.push({
      time: new Date(Date.now() - (29 - i) * 60 * 60 * 1000).toISOString(),
      equity: equity,
    });

    drawdownSeries.push(drawdown);
  }

  return {
    channel: 'portfolio',
    event: 'portfolioUpdate',
    data: {
      balance: 50000,
      equity: 51250.50,
      unrealized_pnl: 1250.50,
      realized_pnl_today: 875.25,
      daily_trades: 15,
      win_rate: 0.67,
      max_drawdown: 1500.00,
      equity_curve: equityCurve,
      drawdown_series: drawdownSeries,
    },
    timestamp: new Date().toISOString(),
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
  };
};

const generateMockBotHeartbeat = () => ({
  channel: 'bot',
  event: 'botHeartbeat',
  data: {
    bot_name: 'NQ Scalper Bot',
    mode: 'paper', // or 'live'
    status: 'healthy',
    uptime_seconds: Math.floor(Math.random() * 3600) + 1800,
    memory_usage_mb: 256 + Math.random() * 128,
    cpu_usage_pct: 15 + Math.random() * 25,
  },
  timestamp: new Date().toISOString(),
  bot_id: '550e8400-e29b-41d4-a716-446655440000',
});

const generateMockPatternDetected = () => ({
  channel: 'patterns',
  event: 'patternDetected',
  data: {
    pattern_id: crypto.randomUUID(),
    pattern_type: ['FVG', 'LIQUIDITY_POOL', 'ORDER_BLOCK'][Math.floor(Math.random() * 3)],
    formation_time: new Date().toISOString(),
    significance: ['MICRO', 'SMALL', 'MEDIUM', 'LARGE', 'EXTREME'][Math.floor(Math.random() * 5)],
    details: {
      gap_high: 20160,
      gap_low: 20155,
      consequent_encroachment: 20157.5,
    },
  },
  timestamp: new Date().toISOString(),
  bot_id: '550e8400-e29b-41d4-a716-446655440000',
});

const generateMockOrderEvent = (status: string) => ({
  channel: 'orders',
  event: `order${status.charAt(0).toUpperCase() + status.slice(1)}`,
  data: {
    order_id: crypto.randomUUID(),
    symbol: 'NQH25',
    side: Math.random() > 0.5 ? 'BUY' : 'SELL',
    quantity: 2,
    order_type: 'LIMIT',
    status,
    price: 20150.50 + Math.random() * 10,
  },
  timestamp: new Date().toISOString(),
  bot_id: '550e8400-e29b-41d4-a716-446655440000',
});

const generateMockCandleComplete = () => ({
  channel: 'orderflow',
  event: 'candleComplete',
  data: {
    timestamp: new Date().toISOString(),
    timeframe: '1min',
    oflow_unit: {
      levels: [
        { price: 20150, buy_vol: 50, sell_vol: 30 },
        { price: 20150.25, buy_vol: 75, sell_vol: 25 },
        { price: 20150.50, buy_vol: 100, sell_vol: 45 },
      ],
    },
    delta: 125,
    poc: 20150.50,
    value_area_high: 20151.00,
    value_area_low: 20150.00,
  },
  timestamp: new Date().toISOString(),
  bot_id: '550e8400-e29b-41d4-a716-446655440000',
});

const generateMockPositionUpdate = () => {
  const side = Math.random() > 0.5 ? 'LONG' : 'SHORT';
  const entryPrice = 20150.00 + Math.random() * 10 - 5;
  const currentPrice = entryPrice + (side === 'LONG' ? 1 : -1) * (Math.random() * 5 - 2);
  const quantity = Math.floor(Math.random() * 3) + 1;
  const unrealizedPnl = side === 'LONG'
    ? (currentPrice - entryPrice) * quantity * 20  // NQ point value is $20
    : (entryPrice - currentPrice) * quantity * 20;

  return {
    channel: 'positions',
    event: 'positionUpdated',
    data: {
      position_id: crypto.randomUUID(),
      symbol: 'NQH25',
      side,
      quantity,
      entry_price: entryPrice,
      current_price: currentPrice,
      unrealized_pnl: unrealizedPnl,
    },
    timestamp: new Date().toISOString(),
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
  };
};

export const websocketHandlers = [
  liveWs.addEventListener('connection', ({ client }) => {
    console.log('[MSW] WebSocket client connected');

    // Send connection established message
    client.send(JSON.stringify({
      session_id: crypto.randomUUID(),
      server_time: new Date().toISOString(),
      version: '1.0.0',
    }));

    // Store subscribed channels
    let subscribedChannels: Set<string> = new Set();
    let intervals: Map<string, NodeJS.Timeout> = new Map();

    // Handle incoming messages
    client.addEventListener('message', (event) => {
      const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
      console.log('[MSW] WebSocket received:', data);

      if (data.action === 'subscribe' && data.channels) {
        // Handle subscription
        data.channels.forEach((channel: string) => {
          subscribedChannels.add(channel);
          console.log(`[MSW] Subscribed to channel: ${channel}`);

          // Start sending mock data based on channel
          switch (channel) {
            case 'price':
              // Send ticks (throttled to 10/sec max as per contract)
              const tickInterval = setInterval(() => {
                if (subscribedChannels.has('price')) {
                  // Send tick with 30% probability to simulate throttling
                  if (Math.random() < 0.3) {
                    client.send(JSON.stringify(generateMockTick()));
                  }
                }
              }, 100); // Check every 100ms but only send 30% of the time
              intervals.set('price-tick', tickInterval);

              // Send bar updates every 5 seconds
              const barInterval = setInterval(() => {
                if (subscribedChannels.has('price')) {
                  client.send(JSON.stringify(generateMockBarUpdate('1min')));
                }
              }, 5000);
              intervals.set('price-bar', barInterval);
              break;

            case 'portfolio':
              // Send portfolio updates every 5 seconds
              const portfolioInterval = setInterval(() => {
                if (subscribedChannels.has('portfolio')) {
                  client.send(JSON.stringify(generateMockPortfolioUpdate()));
                }
              }, 5000);
              intervals.set('portfolio', portfolioInterval);
              break;

            case 'bot':
              // Send bot heartbeat every 30 seconds
              const botInterval = setInterval(() => {
                if (subscribedChannels.has('bot')) {
                  client.send(JSON.stringify(generateMockBotHeartbeat()));
                }
              }, 30000);
              intervals.set('bot', botInterval);

              // Send immediate heartbeat
              client.send(JSON.stringify(generateMockBotHeartbeat()));
              break;

            case 'patterns':
              // Send pattern detection occasionally
              const patternInterval = setInterval(() => {
                if (subscribedChannels.has('patterns') && Math.random() < 0.1) {
                  client.send(JSON.stringify(generateMockPatternDetected()));
                }
              }, 10000);
              intervals.set('patterns', patternInterval);
              break;

            case 'orders':
              // Send order events occasionally
              const orderInterval = setInterval(() => {
                if (subscribedChannels.has('orders') && Math.random() < 0.2) {
                  const statuses = ['submitted', 'filled', 'cancelled'];
                  const status = statuses[Math.floor(Math.random() * statuses.length)];
                  client.send(JSON.stringify(generateMockOrderEvent(status)));
                }
              }, 8000);
              intervals.set('orders', orderInterval);
              break;

            case 'orderflow':
              // Send candle complete every minute
              const oflowInterval = setInterval(() => {
                if (subscribedChannels.has('orderflow')) {
                  client.send(JSON.stringify(generateMockCandleComplete()));
                }
              }, 60000);
              intervals.set('orderflow', oflowInterval);
              break;

            case 'positions':
              // Send position updates (throttled to 1/sec)
              const positionInterval = setInterval(() => {
                if (subscribedChannels.has('positions') && Math.random() < 0.1) {
                  client.send(JSON.stringify(generateMockPositionUpdate()));
                }
              }, 1000);
              intervals.set('positions', positionInterval);
              break;

            case 'risk':
              // Send risk events more frequently for testing

              // Daily loss updates every 5 seconds
              const dailyLossInterval = setInterval(() => {
                if (subscribedChannels.has('risk')) {
                  // Simulate daily loss at 65% (yellow warning zone)
                  client.send(JSON.stringify({
                    channel: 'risk',
                    event: 'daily_loss_update',
                    data: {
                      bot_id: '550e8400-e29b-41d4-a716-446655440000',
                      daily_loss_usd: 1625.50,
                      limit_usd: 2500.00,
                      pct: 65
                    },
                    timestamp: new Date().toISOString(),
                    bot_id: '550e8400-e29b-41d4-a716-446655440000',
                  }));
                }
              }, 5000);
              intervals.set('risk-daily-loss', dailyLossInterval);

              // Trailing drawdown updates every 7 seconds
              const drawdownInterval = setInterval(() => {
                if (subscribedChannels.has('risk')) {
                  // Simulate trailing drawdown at 82% (red danger zone)
                  client.send(JSON.stringify({
                    channel: 'risk',
                    event: 'trailing_drawdown_update',
                    data: {
                      bot_id: '660e8400-e29b-41d4-a716-446655440001',
                      drawdown_usd: 2050.00,
                      threshold_usd: 2500.00,
                      pct: 82
                    },
                    timestamp: new Date().toISOString(),
                    bot_id: '660e8400-e29b-41d4-a716-446655440001',
                  }));
                }
              }, 7000);
              intervals.set('risk-drawdown', drawdownInterval);

              // Risk alerts every 10 seconds
              const alertInterval = setInterval(() => {
                if (subscribedChannels.has('risk')) {
                  const alertLevels = ['INFO', 'WARNING', 'CRITICAL'];
                  const alertMessages = [
                    'Market volatility increasing',
                    'Approaching daily loss limit',
                    'Trailing drawdown nearing threshold',
                    'Circuit breaker armed',
                    'News event in 10 minutes'
                  ];

                  const level = Math.random() < 0.1 ? 'CRITICAL' :
                               Math.random() < 0.3 ? 'WARNING' : 'INFO';

                  client.send(JSON.stringify({
                    channel: 'risk',
                    event: 'risk_alert',
                    data: {
                      level,
                      message: alertMessages[Math.floor(Math.random() * alertMessages.length)],
                      bot_id: Math.random() > 0.5 ? '550e8400-e29b-41d4-a716-446655440000' : '660e8400-e29b-41d4-a716-446655440001'
                    },
                    timestamp: new Date().toISOString(),
                  }));
                }
              }, 10000);
              intervals.set('risk-alerts', alertInterval);

              // Circuit breaker event (rare)
              const circuitBreakerInterval = setInterval(() => {
                if (subscribedChannels.has('risk') && Math.random() < 0.05) {
                  client.send(JSON.stringify({
                    channel: 'risk',
                    event: 'circuit_breaker_triggered',
                    data: {
                      bot_id: '660e8400-e29b-41d4-a716-446655440001',
                      reason: 'Daily loss exceeded 80% threshold',
                      timestamp: new Date().toISOString()
                    },
                    timestamp: new Date().toISOString(),
                    bot_id: '660e8400-e29b-41d4-a716-446655440001',
                  }));
                }
              }, 30000);
              intervals.set('risk-circuit-breaker', circuitBreakerInterval);

              // Send immediate risk status on subscription
              client.send(JSON.stringify({
                channel: 'risk',
                event: 'risk_alert',
                data: {
                  level: 'WARNING',
                  message: 'Risk monitoring activated - Trailing drawdown at 82%',
                  bot_id: '660e8400-e29b-41d4-a716-446655440001'
                },
                timestamp: new Date().toISOString(),
              }));
              break;
          }
        });

        // Send subscription confirmation
        client.send(JSON.stringify({
          action: 'subscribed',
          channels: Array.from(subscribedChannels),
        }));
      }

      if (data.action === 'unsubscribe' && data.channels) {
        // Handle unsubscription
        data.channels.forEach((channel: string) => {
          subscribedChannels.delete(channel);
          console.log(`[MSW] Unsubscribed from channel: ${channel}`);
        });

        // Send unsubscription confirmation
        client.send(JSON.stringify({
          action: 'unsubscribed',
          channels: data.channels,
        }));
      }

      // Handle ping messages (heartbeat)
      if (data.action === 'ping') {
        console.log('[MSW] Received ping, sending pong');
        client.send(JSON.stringify({
          action: 'pong',
          timestamp: new Date().toISOString(),
        }));
      }
    });

    // Heartbeat interval (every 30 seconds)
    let sequence = 0;
    const heartbeatInterval = setInterval(() => {
      client.send(JSON.stringify({
        timestamp: new Date().toISOString(),
        sequence: sequence++,
      }));
    }, 30000);

    // Cleanup on disconnect
    client.addEventListener('close', () => {
      console.log('[MSW] WebSocket client disconnected');
      clearInterval(heartbeatInterval);
      // Clear all channel intervals
      intervals.forEach(interval => clearInterval(interval));
      intervals.clear();
    });
  }),
];

// Example usage for testing kill switch
export const simulateKillSwitch = (client: any) => {
  client.send(JSON.stringify({
    channel: 'risk',
    event: 'killSwitchActivated',
    data: {
      activated_at: new Date().toISOString(),
      reason: 'Manual kill switch activation for testing',
      bots_killed: 3,
      positions_closed: 7,
      orders_cancelled: 12,
      priority: 'HIGHEST',
    },
    timestamp: new Date().toISOString(),
    bot_id: '550e8400-e29b-41d4-a716-446655440000',
  }));
};

// Example page subscription configurations
export const pageSubscriptions = {
  live_dashboard: ['price', 'orderflow', 'patterns', 'orders', 'positions', 'portfolio', 'risk', 'bot'],
  bot_management: ['bot', 'risk'],
  risk_monitor: ['risk', 'portfolio', 'bot'],
  order_management: ['orders', 'positions'],
};