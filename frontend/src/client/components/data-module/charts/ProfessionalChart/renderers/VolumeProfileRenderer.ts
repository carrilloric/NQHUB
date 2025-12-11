import { VolumeProfile, VolumeProfileLevel } from '../types';
import { getVolumeProfileColor, getVAHVALColor, getPOCLineColor } from '../utils/colorMapping';
import { roundToTickSize, NQ_TICK_SIZE } from '../utils/priceUtils';

export interface VolumeProfileRenderOptions {
  width: number;
  maxWidth: number;
  showPOC: boolean;
  showVAH: boolean;
  showVAL: boolean;
}

export class VolumeProfileRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private profile: VolumeProfile | null = null;
  private priceMin: number = 0;
  private priceMax: number = 0;
  private chartHeight: number = 0;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Failed to get 2D context');
    }
    this.ctx = ctx;
  }

  public setDimensions(width: number, height: number, priceMin: number, priceMax: number) {
    this.canvas.width = width;
    this.canvas.height = height;
    this.priceMin = priceMin;
    this.priceMax = priceMax;
    this.chartHeight = height;
  }

  public setProfile(profile: VolumeProfile) {
    this.profile = profile;
  }

  public render(options: VolumeProfileRenderOptions) {
    if (!this.profile) return;

    this.clear();
    this.drawHistogram(options);

    if (options.showVAH) {
      this.drawHorizontalLine(this.profile.vah, getVAHVALColor(), 'VAH');
    }

    if (options.showVAL) {
      this.drawHorizontalLine(this.profile.val, getVAHVALColor(), 'VAL');
    }

    if (options.showPOC) {
      this.drawHorizontalLine(this.profile.poc, getPOCLineColor(), 'POC', true);
    }
  }

  private clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  private drawHistogram(options: VolumeProfileRenderOptions) {
    if (!this.profile) return;

    const maxVolume = Math.max(...this.profile.levels.map(l => l.volume));

    this.profile.levels.forEach(level => {
      const y = this.priceToY(level.price);
      const barWidth = (level.volume / maxVolume) * options.maxWidth;

      // Draw volume bar
      this.ctx.fillStyle = getVolumeProfileColor(0.5);
      this.ctx.fillRect(0, y - 2, barWidth, 4);

      // Draw border
      this.ctx.strokeStyle = getVolumeProfileColor(0.8);
      this.ctx.lineWidth = 1;
      this.ctx.strokeRect(0, y - 2, barWidth, 4);
    });
  }

  private drawHorizontalLine(
    price: number,
    color: string,
    label: string,
    thick: boolean = false
  ) {
    const y = this.priceToY(price);

    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = thick ? 2 : 1;
    this.ctx.setLineDash(thick ? [] : [5, 5]);

    this.ctx.beginPath();
    this.ctx.moveTo(0, y);
    this.ctx.lineTo(this.canvas.width, y);
    this.ctx.stroke();
    this.ctx.setLineDash([]);

    // Draw label
    this.ctx.fillStyle = color;
    this.ctx.font = '10px monospace';
    this.ctx.fillText(label, 5, y - 5);
  }

  private priceToY(price: number): number {
    if (this.priceMax === this.priceMin) return this.chartHeight / 2;

    const priceRange = this.priceMax - this.priceMin;
    const normalizedPrice = (price - this.priceMin) / priceRange;

    // Invert Y axis (higher prices at top)
    return this.chartHeight * (1 - normalizedPrice);
  }

  public destroy() {
    this.clear();
  }
}

/**
 * Calculate volume profile from OHLCV candles
 */
export function calculateVolumeProfile(
  candles: Array<{
    high: number;
    low: number;
    volume: number;
    open: number;
    close: number;
  }>,
  tickSize: number = NQ_TICK_SIZE
): VolumeProfile {
  if (candles.length === 0) {
    return {
      levels: [],
      poc: 0,
      vah: 0,
      val: 0,
      totalVolume: 0,
      valueAreaVolume: 0,
    };
  }

  // Find price range
  const allPrices: number[] = [];
  candles.forEach(c => {
    allPrices.push(c.high, c.low);
  });

  const minPrice = roundToTickSize(Math.min(...allPrices), tickSize);
  const maxPrice = roundToTickSize(Math.max(...allPrices), tickSize);

  // Create volume by price map
  const volumeMap = new Map<number, VolumeProfileLevel>();

  // Initialize all price levels
  for (let price = minPrice; price <= maxPrice; price += tickSize) {
    const roundedPrice = roundToTickSize(price, tickSize);
    volumeMap.set(roundedPrice, {
      price: roundedPrice,
      volume: 0,
      buyVolume: 0,
      sellVolume: 0,
    });
  }

  // Distribute volume across price levels for each candle
  candles.forEach(candle => {
    const candleRange = candle.high - candle.low;
    if (candleRange === 0) return;

    const volumePerTick = candle.volume / (candleRange / tickSize);

    for (let price = candle.low; price <= candle.high; price += tickSize) {
      const roundedPrice = roundToTickSize(price, tickSize);
      const level = volumeMap.get(roundedPrice);

      if (level) {
        level.volume += volumePerTick;

        // Estimate buy/sell volume based on candle direction
        if (candle.close > candle.open) {
          level.buyVolume += volumePerTick * 0.6;
          level.sellVolume += volumePerTick * 0.4;
        } else {
          level.buyVolume += volumePerTick * 0.4;
          level.sellVolume += volumePerTick * 0.6;
        }
      }
    }
  });

  // Convert to array and sort by price
  const levels = Array.from(volumeMap.values()).sort((a, b) => a.price - b.price);

  // Calculate total volume
  const totalVolume = levels.reduce((sum, level) => sum + level.volume, 0);

  // Find POC (Point of Control) - price level with highest volume
  const pocLevel = levels.reduce((max, level) =>
    level.volume > max.volume ? level : max
  );
  const poc = pocLevel.price;

  // Calculate Value Area (70% of volume around POC)
  const valueAreaVolume = totalVolume * 0.7;
  let currentVolume = pocLevel.volume;
  let upperIndex = levels.findIndex(l => l.price === poc);
  let lowerIndex = upperIndex;

  while (currentVolume < valueAreaVolume && (upperIndex < levels.length - 1 || lowerIndex > 0)) {
    const upperVolume = upperIndex < levels.length - 1 ? levels[upperIndex + 1].volume : 0;
    const lowerVolume = lowerIndex > 0 ? levels[lowerIndex - 1].volume : 0;

    if (upperVolume >= lowerVolume && upperIndex < levels.length - 1) {
      upperIndex++;
      currentVolume += upperVolume;
    } else if (lowerIndex > 0) {
      lowerIndex--;
      currentVolume += lowerVolume;
    } else {
      break;
    }
  }

  const vah = levels[upperIndex].price;
  const val = levels[lowerIndex].price;

  return {
    levels,
    poc,
    vah,
    val,
    totalVolume,
    valueAreaVolume: currentVolume,
  };
}
