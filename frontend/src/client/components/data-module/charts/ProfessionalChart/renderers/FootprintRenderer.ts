import { FootprintLevel } from '../types';
import { getHeatmapColor } from '../utils/colorMapping';
import { roundToTickSize, NQ_TICK_SIZE } from '../utils/priceUtils';

// Configuración del layout de velas en modo footprint
const FOOTPRINT_CANDLE_CONFIG = {
  bodyWidthRatio: 0.08,           // 8% del ancho del CELL (vela delgada)
  wickWidth: 2,                   // Grosor del wick en píxeles
  cellWidthRatio: 0.60,           // 60% del ancho original (CELL reducido en 40%)
  timestampPosition: 0.0,         // Timestamp (×) en candle.x
  cellOffsetFromTimestamp: -0.08  // CELL empieza 8% ANTES del timestamp (cubre números)
};

export interface FootprintRenderOptions {
  showNumbers: boolean;
  showHeatmap: boolean;
  showDelta: boolean;
  showPOCBorder: boolean;
  fontSize: number;
  cellHeight: number;
  isDarkTheme: boolean; // For theme-specific rendering
}

export interface FootprintCandleData {
  x: number; // X position on chart
  width: number; // Width of candle
  levels: FootprintLevel[];
  delta: number;
  volume: number;
  open: number;  // Added for candle rendering
  high: number;
  low: number;
  close: number; // Added for candle rendering
}

export class FootprintRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private chartHeight: number = 0;
  private priceMin: number = 0;
  private priceMax: number = 0;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Failed to get 2D context for FootprintRenderer');
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

  public render(candles: FootprintCandleData[], options: FootprintRenderOptions) {
    this.clear();

    // First pass: Draw candlesticks
    candles.forEach(candle => {
      this.renderCandlestick(candle, options.isDarkTheme);
    });

    // Second pass: Draw footprint overlays
    candles.forEach(candle => {
      this.renderFootprint(candle, options);
    });
  }

  private clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  private renderCandlestick(candle: FootprintCandleData, isDarkTheme: boolean) {
    const { x, width, open, high, low, close } = candle;
    const openY = this.priceToY(open);
    const closeY = this.priceToY(close);
    const highY = this.priceToY(high);
    const lowY = this.priceToY(low);

    const isBullish = close > open;
    const color = isBullish ? '#26a69a' : '#ef5350';

    // Calculate CELL width (reduced to 60% of original)
    const cellWidth = width * FOOTPRINT_CANDLE_CONFIG.cellWidthRatio;

    // FIXED timestamp position (where × text is displayed)
    const timestampX = x + width * FOOTPRINT_CANDLE_CONFIG.timestampPosition;

    // CELL starts BEFORE timestamp to cover numbers
    const cellStartX = timestampX + width * FOOTPRINT_CANDLE_CONFIG.cellOffsetFromTimestamp;

    // Calculate candle position: right edge aligned with CELL left edge
    const bodyWidth = cellWidth * FOOTPRINT_CANDLE_CONFIG.bodyWidthRatio;
    const bodyX = cellStartX - bodyWidth; // Vela pegada al inicio del CELL

    // Calculate wick position: center of the candle body
    const candleWickX = bodyX + bodyWidth / 2;

    // Draw wick (high to low) - centered on candle
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = FOOTPRINT_CANDLE_CONFIG.wickWidth;
    this.ctx.beginPath();
    this.ctx.moveTo(candleWickX, highY);
    this.ctx.lineTo(candleWickX, lowY);
    this.ctx.stroke();

    // Draw body
    const bodyTop = Math.min(openY, closeY);
    const bodyHeight = Math.abs(closeY - openY);

    this.ctx.fillStyle = color;
    this.ctx.fillRect(bodyX, bodyTop, bodyWidth, bodyHeight || 1);
  }

  private renderFootprint(candle: FootprintCandleData, options: FootprintRenderOptions) {
    if (candle.levels.length === 0) return;

    // Calculate CELL width (reduced to 60% of original)
    const cellWidth = candle.width * FOOTPRINT_CANDLE_CONFIG.cellWidthRatio;

    // FIXED timestamp position (where × text is displayed)
    const timestampX = candle.x + candle.width * FOOTPRINT_CANDLE_CONFIG.timestampPosition;

    // CELL starts BEFORE timestamp to cover numbers
    const cellStartX = timestampX + candle.width * FOOTPRINT_CANDLE_CONFIG.cellOffsetFromTimestamp;

    // Find max volume for scaling horizontal bars
    const maxVolume = Math.max(...candle.levels.map(l => l.totalVolume));

    // Render each price level
    candle.levels.forEach(level => {
      const y = this.priceToY(level.price);
      const cellHeight = options.cellHeight;
      const cellY = y - cellHeight / 2;

      // 1. Draw semi-transparent cell background based on dominance
      const bidDominant = level.bidVolume > level.askVolume;
      const askDominant = level.askVolume > level.bidVolume;

      if (bidDominant) {
        // Green semi-transparent for bid dominance (reduced opacity)
        this.ctx.fillStyle = 'rgba(38, 166, 154, 0.08)';
        this.ctx.fillRect(cellStartX, cellY, cellWidth, cellHeight);
      } else if (askDominant) {
        // Red semi-transparent for ask dominance (reduced opacity)
        this.ctx.fillStyle = 'rgba(239, 83, 80, 0.08)';
        this.ctx.fillRect(cellStartX, cellY, cellWidth, cellHeight);
      }

      // 2. Draw horizontal volume bar on the LEFT side
      const barMaxWidth = cellWidth * 0.3; // 30% of cell width
      const volumeRatio = level.totalVolume / maxVolume;
      const barWidth = barMaxWidth * volumeRatio;

      if (barWidth > 0) {
        const barColor = bidDominant ? '#26a69a' : askDominant ? '#ef5350' : '#888888';
        this.ctx.fillStyle = barColor;
        this.ctx.fillRect(cellStartX, cellY, barWidth, cellHeight);
      }

      // 3. Draw POC border - thick black border for visibility (drawn LAST for z-order)
      if (options.showPOCBorder && level.isPOC) {
        this.ctx.save();
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 4; // Thick border like in reference image
        this.ctx.globalAlpha = 1; // Ensure full opacity for POC border

        // Draw border slightly inset to ensure visibility
        const inset = 1;
        this.ctx.strokeRect(
          cellStartX + inset,
          cellY + inset,
          cellWidth - inset * 2,
          cellHeight - inset * 2
        );
        this.ctx.restore();
      }

      // 4. Draw bid x ask numbers at timestamp position
      if (options.showNumbers) {
        this.drawBidAskNumbers(
          level,
          timestampX,
          y,
          options.fontSize,
          options.isDarkTheme
        );
      }
    });

    // Draw delta and volume totals below candle
    if (options.showDelta) {
      this.drawCandleTotals(candle, timestampX, options);
    }
  }

  private drawBidAskNumbers(
    level: FootprintLevel,
    timestampX: number,
    y: number,
    fontSize: number,
    isDarkTheme: boolean
  ) {
    this.ctx.font = `bold ${fontSize}px monospace`;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';

    // Format numbers (abbreviate if large)
    const formatVolume = (vol: number): string => {
      if (vol >= 1000) {
        return `${(vol / 1000).toFixed(1)}k`;
      }
      return vol.toString();
    };

    const bidStr = formatVolume(level.bidVolume);
    const askStr = formatVolume(level.askVolume);
    const text = `${bidStr}×${askStr}`;

    // Position: aligned with timestamp
    const centerX = timestampX;

    if (isDarkTheme) {
      // Dark theme: White text with black outline
      this.ctx.strokeStyle = '#000000';
      this.ctx.lineWidth = 3;
      this.ctx.strokeText(text, centerX, y);

      this.ctx.fillStyle = '#ffffff';
      this.ctx.fillText(text, centerX, y);
    } else {
      // Light theme: Pure black text, NO outline
      this.ctx.fillStyle = '#000000';
      this.ctx.fillText(text, centerX, y);
    }
  }

  private drawCandleTotals(candle: FootprintCandleData, timestampX: number, options: FootprintRenderOptions) {
    const bottomY = this.priceToY(candle.low) + 15;

    this.ctx.font = `${options.fontSize}px monospace`;
    this.ctx.textAlign = 'center';

    // Draw delta
    const deltaColor = candle.delta >= 0 ? '#26a69a' : '#ef5350';
    this.ctx.fillStyle = deltaColor;

    const deltaText = candle.delta >= 0 ? `+${candle.delta}` : `${candle.delta}`;
    this.ctx.fillText(deltaText, timestampX, bottomY);

    // Draw volume below delta
    this.ctx.fillStyle = '#d1d4dc';
    this.ctx.fillText(`V:${candle.volume}`, timestampX, bottomY + 12);
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
 * Calculate appropriate cell height based on price range and chart height
 */
export function calculateFootprintCellHeight(
  priceMin: number,
  priceMax: number,
  chartHeight: number,
  tickSize: number = NQ_TICK_SIZE
): number {
  const priceRange = priceMax - priceMin;
  const numberOfTicks = priceRange / tickSize;

  // Cell height should allow all ticks to be visible
  const calculatedHeight = chartHeight / numberOfTicks;

  // Clamp between reasonable values - minimum 18px for readability
  return Math.max(18, Math.min(40, calculatedHeight));
}

/**
 * Determine if candle is wide enough to show footprint
 */
export function shouldShowFootprint(candleWidth: number, minWidth: number = 30): boolean {
  return candleWidth >= minWidth;
}
