import React, { useEffect, useRef } from 'react';
import {
  FootprintRenderer,
  FootprintCandleData,
  FootprintRenderOptions,
  calculateFootprintCellHeight,
} from '../renderers/FootprintRenderer';

export interface FootprintProps {
  candles: FootprintCandleData[];
  width: number;
  height: number;
  priceMin: number;
  priceMax: number;
  showNumbers?: boolean;
  showHeatmap?: boolean;
  showDelta?: boolean;
  showPOCBorder?: boolean;
  fontSize?: number;
  isDarkTheme?: boolean;
}

export const Footprint: React.FC<FootprintProps> = ({
  candles,
  width,
  height,
  priceMin,
  priceMax,
  showNumbers = true,
  showHeatmap = true,
  showDelta = true,
  showPOCBorder = true,
  fontSize = 10,
  isDarkTheme = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<FootprintRenderer | null>(null);

  // Initialize renderer
  useEffect(() => {
    if (!canvasRef.current) return;

    rendererRef.current = new FootprintRenderer(canvasRef.current);

    return () => {
      rendererRef.current?.destroy();
    };
  }, []);

  // Update dimensions
  useEffect(() => {
    if (!rendererRef.current) return;

    rendererRef.current.setDimensions(width, height, priceMin, priceMax);
  }, [width, height, priceMin, priceMax]);

  // Render footprint
  useEffect(() => {
    if (!rendererRef.current || candles.length === 0) return;

    const cellHeight = calculateFootprintCellHeight(priceMin, priceMax, height);

    const options: FootprintRenderOptions = {
      showNumbers,
      showHeatmap,
      showDelta,
      showPOCBorder,
      fontSize,
      cellHeight,
      isDarkTheme,
    };

    rendererRef.current.render(candles, options);
  }, [candles, showNumbers, showHeatmap, showDelta, showPOCBorder, fontSize, priceMin, priceMax, height, isDarkTheme]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        pointerEvents: 'none',
        zIndex: 20,
      }}
    />
  );
};
