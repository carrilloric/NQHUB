/**
 * CircuitBreakerStatus Component
 *
 * Displays active circuit breakers for a bot.
 */
import React from 'react';
import { cn } from '@/lib/utils';

interface CircuitBreaker {
  name: string;
  active: boolean;
  threshold: number;
  current_value: number;
}

interface CircuitBreakerStatusProps {
  circuitBreakers: CircuitBreaker[];
  className?: string;
}

export function CircuitBreakerStatus({
  circuitBreakers,
  className,
}: CircuitBreakerStatusProps) {
  if (circuitBreakers.length === 0) {
    return (
      <div className={cn('text-sm text-gray-500 dark:text-gray-400', className)}>
        No circuit breakers active
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
        Circuit Breakers
      </h4>
      <div className="space-y-1">
        {circuitBreakers.map((cb, index) => (
          <div
            key={index}
            className={cn(
              'flex items-center justify-between px-3 py-2 rounded-md text-sm',
              cb.active
                ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
            )}
          >
            <span className="font-medium">{cb.name}</span>
            <span className={cn('text-xs', cb.active && 'font-semibold')}>
              {cb.active ? '🔴 ACTIVE' : '🟢 Inactive'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
