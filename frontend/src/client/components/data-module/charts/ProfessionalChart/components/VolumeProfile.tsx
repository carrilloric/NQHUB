import React, { useEffect, useRef } from 'react';
import { VolumeProfileRenderer, calculateVolumeProfile } from '../renderers/VolumeProfileRenderer';
import type { VolumeProfile as VolumeProfileType } from '../types';

export interface VolumeProfileProps {
  candles: Array<{
    high: number;
    low: number;
    volume: number;
    open: number;
    close: number;
  }>;
  width?: number;
  height: number;
  priceMin: number;
  priceMax: number;
  showPOC?: boolean;
  showVAH?: boolean;
  showVAL?: boolean;
}

export const VolumeProfile: React.FC<VolumeProfileProps> = ({
  candles,
  width = 150,
  height,
  priceMin,
  priceMax,
  showPOC = true,
  showVAH = true,
  showVAL = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<VolumeProfileRenderer | null>(null);
  const profileRef = useRef<VolumeProfileType | null>(null);

  // Initialize renderer
  useEffect(() => {
    if (!canvasRef.current) return;

    rendererRef.current = new VolumeProfileRenderer(canvasRef.current);

    return () => {
      rendererRef.current?.destroy();
    };
  }, []);

  // Update dimensions
  useEffect(() => {
    if (!rendererRef.current) return;

    rendererRef.current.setDimensions(width, height, priceMin, priceMax);
  }, [width, height, priceMin, priceMax]);

  // Calculate and render profile
  useEffect(() => {
    if (!rendererRef.current || candles.length === 0) return;

    // Calculate volume profile
    profileRef.current = calculateVolumeProfile(candles);
    rendererRef.current.setProfile(profileRef.current);

    // Render
    rendererRef.current.render({
      width,
      maxWidth: width * 0.9, // 90% of available width for bars
      showPOC,
      showVAH,
      showVAL,
    });
  }, [candles, width, showPOC, showVAH, showVAL]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        pointerEvents: 'none',
        zIndex: 25, // Above footprint (20) to stay visible
      }}
    />
  );
};
