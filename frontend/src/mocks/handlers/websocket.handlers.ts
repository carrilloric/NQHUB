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

const generateMockPortfolioUpdate = () => ({
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
  },
  timestamp: new Date().toISOString(),
  bot_id: '550e8400-e29b-41d4-a716-446655440000',
});

const generateMockBotHeartbeat = () => ({
  channel: 'bot',
  event: 'botHeartbeat',
  data: {
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
                  client.send(JSON.stringify({
                    channel: 'positions',
                    event: 'positionUpdated',
                    data: {
                      position_id: crypto.randomUUID(),
                      symbol: 'NQH25',
                      side: 'LONG',
                      quantity: 2,
                      entry_price: 20150.00,
                      current_price: 20152.50,
                      unrealized_pnl: 125.00,
                    },
                    timestamp: new Date().toISOString(),
                    bot_id: '550e8400-e29b-41d4-a716-446655440000',
                  }));
                }
              }, 1000);
              intervals.set('positions', positionInterval);
              break;

            case 'risk':
              // Send risk events very occasionally
              const riskInterval = setInterval(() => {
                if (subscribedChannels.has('risk') && Math.random() < 0.01) {
                  // Very rare circuit breaker event
                  client.send(JSON.stringify({
                    channel: 'risk',
                    event: 'circuitBreakerTriggered',
                    data: {
                      triggered_at: new Date().toISOString(),
                      reason: 'Daily loss limit approaching (90%)',
                      threshold_exceeded: 'daily_loss',
                      actions_taken: ['stopped_new_orders'],
                    },
                    timestamp: new Date().toISOString(),
                    bot_id: '550e8400-e29b-41d4-a716-446655440000',
                  }));
                }
              }, 30000);
              intervals.set('risk', riskInterval);
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