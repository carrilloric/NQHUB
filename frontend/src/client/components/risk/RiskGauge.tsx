/**
 * RiskGauge Component
 *
 * Circular gauge for displaying risk metrics with color-coded thresholds.
 *
 * Color logic:
 * - <70% of limit: Green (#22c55e)
 * - 70-90% of limit: Yellow (#f59e0b) warning
 * - >90% of limit: Red (#ef4444) danger with pulse animation
 * - 100% breach: Red with pulsating animation + auto kill switch trigger
 */
import React from 'react';
import { cn } from '@/lib/utils';

interface RiskGaugeProps {
  /** Display label (e.g., "Daily Loss", "Trailing Drawdown") */
  label: string;

  /** Current value (e.g., -450 for daily loss of $450) */
  value: number;

  /** Maximum limit (e.g., 1000 for max daily loss of $1000) */
  limit: number;

  /** Display format */
  format: 'currency' | 'percent';

  /** Optional className for container */
  className?: string;
}

/**
 * Calculate percentage of limit used
 */
function calculatePercentage(value: number, limit: number): number {
  if (limit === 0) return 0;

  // For daily loss (negative values), use absolute value
  const absValue = Math.abs(value);
  return (absValue / limit) * 100;
}

/**
 * Get color based on threshold percentage
 */
function getColorClasses(percentage: number): {
  text: string;
  fill: string;
  ring: string;
  shouldPulse: boolean;
} {
  if (percentage < 70) {
    return {
      text: 'text-green-600',
      fill: 'fill-green-600',
      ring: 'ring-green-500',
      shouldPulse: false,
    };
  }

  if (percentage < 90) {
    return {
      text: 'text-yellow-600',
      fill: 'fill-yellow-600',
      ring: 'ring-yellow-500',
      shouldPulse: false,
    };
  }

  // >90% - red with pulse
  return {
    text: 'text-red-600',
    fill: 'fill-red-600',
    ring: 'ring-red-500',
    shouldPulse: true,
  };
}

/**
 * Format value based on format type
 */
function formatValue(value: number, format: 'currency' | 'percent'): string {
  if (format === 'currency') {
    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '+';
    return `${sign}$${absValue.toFixed(2)}`;
  }

  return `${value.toFixed(1)}%`;
}

export function RiskGauge({ label, value, limit, format, className }: RiskGaugeProps) {
  const percentage = calculatePercentage(value, limit);
  const colors = getColorClasses(percentage);

  // Calculate SVG arc path for gauge
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // Clamp percentage to 100% for display
  const displayPercentage = Math.min(percentage, 100);

  return (
    <div className={cn('flex flex-col items-center space-y-2', className)}>
      {/* Gauge Label */}
      <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </div>

      {/* SVG Gauge */}
      <div className="relative w-40 h-40">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
          {/* Background circle */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="currentColor"
            strokeWidth="12"
            fill="none"
            className="text-gray-200 dark:text-gray-700"
          />

          {/* Progress arc */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="currentColor"
            strokeWidth="12"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={cn(
              'transition-all duration-500',
              colors.text,
              colors.shouldPulse && 'animate-pulse'
            )}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={cn('text-2xl font-bold', colors.text)}>
            {displayPercentage.toFixed(0)}%
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {formatValue(value, format)}
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500">
            of {formatValue(limit, format)}
          </div>
        </div>
      </div>

      {/* Warning badge if >90% */}
      {colors.shouldPulse && (
        <div
          className={cn(
            'px-3 py-1 rounded-full text-xs font-semibold',
            'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
            'animate-pulse'
          )}
        >
          ⚠️ DANGER ZONE
        </div>
      )}

      {/* Info badge if 70-90% */}
      {percentage >= 70 && percentage < 90 && (
        <div className="px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200">
          ⚠️ WARNING
        </div>
      )}
    </div>
  );
}
