/**
 * MSW Data Explorer Handlers
 *
 * Mock handlers for Data Explorer API endpoints based on CONTRACT-001
 */

import { http, HttpResponse } from 'msw';
import { addDays, subDays, format, parseISO } from 'date-fns';

const API_BASE = '/api/v1';

// Helper functions to generate mock data
const generateCandle = (timestamp: Date, basePrice: number = 20150.00) => {
  const open = basePrice + (Math.random() - 0.5) * 10;
  const close = open + (Math.random() - 0.5) * 8;
  const high = Math.max(open, close) + Math.random() * 5;
  const low = Math.min(open, close) - Math.random() * 5;
  const volume = Math.floor(Math.random() * 1000) + 500;
  const buyVolume = Math.floor(volume * (0.4 + Math.random() * 0.2));
  const sellVolume = volume - buyVolume;
  const delta = buyVolume - sellVolume;

  return {
    timestamp: timestamp.toISOString(),
    open: parseFloat(open.toFixed(2)),
    high: parseFloat(high.toFixed(2)),
    low: parseFloat(low.toFixed(2)),
    close: parseFloat(close.toFixed(2)),
    volume,
    // Orderflow metrics
    delta,
    buy_volume: buyVolume,
    sell_volume: sellVolume,
    cumulative_delta: delta * 2,
    buy_trades: Math.floor(buyVolume / 10),
    sell_trades: Math.floor(sellVolume / 10),
    delta_percentage: parseFloat(((delta / volume) * 100).toFixed(2)),
    max_delta: delta + Math.floor(Math.random() * 50),
    min_delta: delta - Math.floor(Math.random() * 50),
    delta_change: Math.floor((Math.random() - 0.5) * 100),
    // Price levels & statistics
    vwap: parseFloat(((high + low + close) / 3).toFixed(2)),
    typical_price: parseFloat(((high + low + close) / 3).toFixed(2)),
    range: parseFloat((high - low).toFixed(2)),
    body_size: parseFloat(Math.abs(open - close).toFixed(2)),
    wick_upper: parseFloat((high - Math.max(open, close)).toFixed(2)),
    wick_lower: parseFloat((Math.min(open, close) - low).toFixed(2)),
    body_percentage: parseFloat((Math.abs(open - close) / (high - low) * 100).toFixed(2)),
    price_change: parseFloat((close - open).toFixed(2)),
    price_change_percentage: parseFloat(((close - open) / open * 100).toFixed(2)),
    cumulative_volume: volume * 10,
    // Market microstructure
    tick_count: Math.floor(Math.random() * 200) + 100,
    bid_volume: Math.floor(buyVolume * 0.8),
    ask_volume: Math.floor(sellVolume * 0.8),
    imbalance: parseFloat(((buyVolume - sellVolume) / (buyVolume + sellVolume)).toFixed(3)),
    spread_avg: parseFloat((0.25 + Math.random() * 0.25).toFixed(2)),
    trade_intensity: parseFloat((Math.random() * 0.5).toFixed(3)),
    volume_rate: parseFloat((Math.random() * 10).toFixed(2)),
    large_trade_count: Math.floor(Math.random() * 10),
    large_trade_volume: Math.floor(Math.random() * 500),
  };
};

const generateCandles = (startDate: string, endDate: string, timeframe: string, limit: number = 100) => {
  const candles = [];
  let currentDate = parseISO(startDate);
  const end = parseISO(endDate);
  let basePrice = 20150.00;

  // Calculate interval based on timeframe
  let intervalMinutes = 1;
  switch (timeframe) {
    case '1min': intervalMinutes = 1; break;
    case '5min': intervalMinutes = 5; break;
    case '15min': intervalMinutes = 15; break;
    case '30min': intervalMinutes = 30; break;
    case '1hour': intervalMinutes = 60; break;
    case '4hour': intervalMinutes = 240; break;
    case '1day': intervalMinutes = 1440; break;
  }

  while (currentDate <= end && candles.length < limit) {
    const candle = generateCandle(currentDate, basePrice);
    candles.push(candle);
    // Update base price for next candle (trending effect)
    basePrice = candle.close + (Math.random() - 0.5) * 2;
    currentDate = new Date(currentDate.getTime() + intervalMinutes * 60000);
  }

  return candles;
};

const generateCoverageData = () => {
  const timeframes = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day'];
  return timeframes.map((tf) => {
    const endDate = new Date();
    const startDate = subDays(endDate, Math.floor(Math.random() * 90) + 30);
    const count = Math.floor(Math.random() * 50000) + 10000;

    return {
      tf,
      count,
      start: startDate.toISOString(),
      end: endDate.toISOString(),
      last_updated: new Date().toISOString(),
    };
  });
};

const generateContracts = () => {
  const months = ['H', 'M', 'U', 'Z']; // March, June, September, December
  const year = new Date().getFullYear().toString().slice(-2);
  const currentMonth = new Date().getMonth();
  const currentQuarter = Math.floor(currentMonth / 3);

  return months.map((month, index) => {
    const isFront = index === currentQuarter;
    const expiryMonth = (index * 3) + 2; // March=2, June=5, September=8, December=11
    const expiryYear = expiryMonth < currentMonth ? parseInt(year) + 1 : parseInt(year);
    const expiryDate = new Date(2000 + expiryYear, expiryMonth, 15); // Third Friday approximation

    return {
      symbol: `NQ${month}${expiryYear}`,
      expiry: format(expiryDate, 'yyyy-MM-dd'),
      is_front_month: isFront,
    };
  });
};

// Export job tracking
const exportJobs = new Map<string, any>();

export const dataExplorerHandlers = [
  // Get candles by timeframe
  http.get(`${API_BASE}/data/candles/:tf`, ({ request, params }) => {
    const url = new URL(request.url);
    const tf = params.tf as string;
    const symbol = url.searchParams.get('symbol') || 'NQH25';
    const start = url.searchParams.get('start') || format(subDays(new Date(), 7), 'yyyy-MM-dd');
    const end = url.searchParams.get('end') || format(new Date(), 'yyyy-MM-dd');
    const includeOflow = url.searchParams.get('include_oflow') === 'true';
    const limit = parseInt(url.searchParams.get('limit') || '100');
    const offset = parseInt(url.searchParams.get('offset') || '0');

    const allCandles = generateCandles(start, end, tf, limit + offset + 100);
    const paginatedCandles = allCandles.slice(offset, offset + limit);

    return HttpResponse.json({
      data: paginatedCandles,
      total: allCandles.length,
      has_more: allCandles.length > offset + limit,
    });
  }),

  // Get specific candle by timestamp
  http.get(`${API_BASE}/data/candles/:tf/:timestamp`, ({ params }) => {
    const timestamp = params.timestamp as string;
    const candle = generateCandle(new Date(timestamp));

    return HttpResponse.json({
      ...candle,
      oflow_detail: {
        price_levels: Array.from({ length: 10 }, (_, i) => ({
          price: candle.low + (i * (candle.high - candle.low) / 10),
          bid_volume: Math.floor(Math.random() * 100),
          ask_volume: Math.floor(Math.random() * 100),
          trades: Math.floor(Math.random() * 20),
        })),
      },
    });
  }),

  // Get tick data
  http.get(`${API_BASE}/data/ticks`, ({ request }) => {
    const url = new URL(request.url);
    const start = url.searchParams.get('start') || format(subDays(new Date(), 1), 'yyyy-MM-dd');
    const end = url.searchParams.get('end') || format(new Date(), 'yyyy-MM-dd');
    const limit = parseInt(url.searchParams.get('limit') || '100');

    const ticks = Array.from({ length: limit }, (_, i) => {
      const timestamp = new Date(parseISO(start).getTime() + i * 1000);
      const price = 20150 + (Math.random() - 0.5) * 10;
      return {
        timestamp: timestamp.toISOString(),
        price: parseFloat(price.toFixed(2)),
        size: Math.floor(Math.random() * 10) + 1,
        side: Math.random() > 0.5 ? 'buy' : 'sell',
        bid: parseFloat((price - 0.25).toFixed(2)),
        ask: parseFloat((price + 0.25).toFixed(2)),
      };
    });

    return HttpResponse.json({
      data: ticks,
      total: ticks.length,
    });
  }),

  // Get coverage information
  http.get(`${API_BASE}/data/coverage`, () => {
    return HttpResponse.json({
      timeframes: generateCoverageData(),
    });
  }),

  // Get active contracts
  http.get(`${API_BASE}/data/contracts/active`, () => {
    return HttpResponse.json({
      contracts: generateContracts(),
    });
  }),

  // Get rollover periods
  http.get(`${API_BASE}/data/rollover-periods`, () => {
    const rollovers = [
      {
        from_symbol: 'NQZ24',
        to_symbol: 'NQH25',
        rollover_date: '2024-12-13',
      },
      {
        from_symbol: 'NQH25',
        to_symbol: 'NQM25',
        rollover_date: '2025-03-14',
      },
      {
        from_symbol: 'NQM25',
        to_symbol: 'NQU25',
        rollover_date: '2025-06-13',
      },
    ];

    return HttpResponse.json({
      rollovers,
    });
  }),

  // Create export job
  http.post(`${API_BASE}/data/export`, async ({ request }) => {
    const body = await request.json() as any;
    const jobId = crypto.randomUUID();

    // Store job info
    exportJobs.set(jobId, {
      ...body,
      job_id: jobId,
      status: 'queued',
      created_at: new Date().toISOString(),
      progress: 0,
    });

    // Simulate processing after 1 second
    setTimeout(() => {
      const job = exportJobs.get(jobId);
      if (job) {
        job.status = 'processing';
        job.progress = 0;

        // Simulate progress updates
        let progress = 0;
        const interval = setInterval(() => {
          progress += 20;
          job.progress = progress;

          if (progress >= 100) {
            clearInterval(interval);
            job.status = 'complete';
            job.download_url = `https://downloads.nqhub.com/exports/${jobId}.${body.format}`;
            job.size_mb = parseFloat((Math.random() * 100 + 10).toFixed(2));
          }
        }, 500);
      }
    }, 1000);

    return HttpResponse.json(
      {
        job_id: jobId,
        status: 'queued',
      },
      { status: 201 }
    );
  }),

  // Get export job status
  http.get(`${API_BASE}/data/export/:job_id`, ({ params }) => {
    const jobId = params.job_id as string;
    const job = exportJobs.get(jobId);

    if (!job) {
      return HttpResponse.json(
        { detail: 'Export job not found' },
        { status: 404 }
      );
    }

    const response: any = {
      status: job.status,
      progress: job.progress,
    };

    if (job.status === 'complete') {
      response.download_url = job.download_url;
      response.size_mb = job.size_mb;
    } else if (job.status === 'failed') {
      response.error_message = 'Export failed due to insufficient data';
    }

    return HttpResponse.json(response);
  }),
];