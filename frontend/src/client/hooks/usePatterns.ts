import { useState, useEffect } from 'react';

export interface FVGPattern {
  id: string;
  timestamp: string;
  direction: 'bullish' | 'bearish';
  top: number;
  bottom: number;
  size_ticks: number;
  status: 'active' | 'mitigated' | 'broken';
  timeframe: string;
}

export interface OrderBlockPattern {
  id: string;
  timestamp: string;
  direction: 'bullish' | 'bearish';
  top: number;
  bottom: number;
  strength: 'weak' | 'medium' | 'strong';
  status: 'active' | 'tested' | 'broken';
  timeframe: string;
}

export interface LiquidityPoolPattern {
  id: string;
  timestamp: string;
  side: 'buy' | 'sell';
  price: number;
  size: number;
  status: 'active' | 'swept' | 'mitigated';
  timeframe: string;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface UsePatternsOptions {
  timeframe: string;
  dateRange?: DateRange;
  status?: string;
}

export function usePatterns(options: UsePatternsOptions) {
  const { timeframe, dateRange, status = 'all' } = options;

  const [fvgs, setFvgs] = useState<FVGPattern[]>([]);
  const [orderBlocks, setOrderBlocks] = useState<OrderBlockPattern[]>([]);
  const [liquidityPools, setLiquidityPools] = useState<LiquidityPoolPattern[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchPatterns = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams({
          timeframe,
          ...(status !== 'all' && { status }),
          ...(dateRange?.start && { start: dateRange.start }),
          ...(dateRange?.end && { end: dateRange.end }),
        });

        // Fetch FVGs
        const fvgResponse = await fetch(`/api/v1/patterns/fvg?${params}`);
        if (!fvgResponse.ok) throw new Error('Failed to fetch FVGs');
        const fvgData = await fvgResponse.json();
        setFvgs(fvgData.patterns || []);

        // Fetch Order Blocks
        const obResponse = await fetch(`/api/v1/patterns/ob?${params}`);
        if (!obResponse.ok) throw new Error('Failed to fetch Order Blocks');
        const obData = await obResponse.json();
        setOrderBlocks(obData.patterns || []);

        // Fetch Liquidity Pools
        const lpResponse = await fetch(`/api/v1/patterns/lp?${params}`);
        if (!lpResponse.ok) throw new Error('Failed to fetch Liquidity Pools');
        const lpData = await lpResponse.json();
        setLiquidityPools(lpData.patterns || []);
      } catch (err) {
        setError(err as Error);
        console.error('Error fetching patterns:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPatterns();
  }, [timeframe, status, dateRange?.start, dateRange?.end]);

  return {
    fvgs,
    orderBlocks,
    liquidityPools,
    isLoading,
    error,
  };
}