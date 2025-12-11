import { DEFAULT_COLOR_SCHEME } from '../types';

/**
 * Color mapping utilities for footprint visualization
 */

export function getVolumeColor(
  bidVolume: number,
  askVolume: number,
  threshold: number = 1.5
): string {
  const total = bidVolume + askVolume;
  if (total === 0) return DEFAULT_COLOR_SCHEME.neutral;

  const imbalance = Math.max(bidVolume, askVolume) / Math.min(bidVolume, askVolume);

  if (imbalance < threshold) {
    return DEFAULT_COLOR_SCHEME.neutral;
  }

  return bidVolume > askVolume
    ? DEFAULT_COLOR_SCHEME.bullish
    : DEFAULT_COLOR_SCHEME.bearish;
}

export function getVolumeColorWithAlpha(
  bidVolume: number,
  askVolume: number,
  maxVolume: number,
  threshold: number = 1.5
): string {
  const baseColor = getVolumeColor(bidVolume, askVolume, threshold);
  const totalVolume = bidVolume + askVolume;
  const intensity = maxVolume > 0 ? Math.min(totalVolume / maxVolume, 1) : 0;

  // Convert hex to rgba with calculated alpha
  const alpha = 0.2 + intensity * 0.6; // Range from 0.2 to 0.8

  return hexToRgba(baseColor, alpha);
}

export function getDeltaColor(delta: number): string {
  if (delta > 0) return DEFAULT_COLOR_SCHEME.bullish;
  if (delta < 0) return DEFAULT_COLOR_SCHEME.bearish;
  return DEFAULT_COLOR_SCHEME.neutral;
}

export function getPOCBorderColor(): string {
  return DEFAULT_COLOR_SCHEME.pocBorder;
}

export function getTextColor(
  bidVolume: number,
  askVolume: number
): string {
  // Return white for dark backgrounds, adjust based on volume dominance
  const total = bidVolume + askVolume;
  if (total === 0) return '#ffffff';

  return '#ffffff';
}

export function hexToRgba(hex: string, alpha: number): string {
  // Remove # if present
  const cleanHex = hex.replace('#', '');

  // Parse hex values
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function getVolumeProfileColor(alpha: number = 0.5): string {
  // Blue color for volume profile (#2962ff)
  return `rgba(41, 98, 255, ${alpha})`;
}

export function getVAHVALColor(): string {
  return '#758696'; // Gray for VAH/VAL lines
}

export function getPOCLineColor(): string {
  return '#ffeb3b'; // Yellow for POC line
}

export function getCrosshairColor(): string {
  return '#758696';
}

export function getGridColor(): string {
  return DEFAULT_COLOR_SCHEME.grid;
}

/**
 * Get color intensity based on volume relative to max
 */
export function getColorIntensity(volume: number, maxVolume: number): number {
  if (maxVolume === 0) return 0;
  return Math.min(volume / maxVolume, 1);
}

/**
 * Generate heatmap color based on volume intensity
 */
export function getHeatmapColor(
  bidVolume: number,
  askVolume: number,
  maxVolume: number,
  isPOC: boolean = false
): { backgroundColor: string; textColor: string; border?: string } {
  if (isPOC) {
    return {
      backgroundColor: getVolumeColorWithAlpha(bidVolume, askVolume, maxVolume, 1.5),
      textColor: '#ffffff',
      border: `2px solid ${DEFAULT_COLOR_SCHEME.pocBorder}`,
    };
  }

  return {
    backgroundColor: getVolumeColorWithAlpha(bidVolume, askVolume, maxVolume, 1.5),
    textColor: getTextColor(bidVolume, askVolume),
  };
}
