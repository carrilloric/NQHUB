/**
 * Positions Table Component
 *
 * Displays open positions with real-time updates
 */

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowUpIcon, ArrowDownIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Position {
  position_id?: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
}

interface PositionsTableProps {
  positions: Position[];
}

export default function PositionsTable({ positions }: PositionsTableProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  if (positions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No open positions</p>
        <p className="text-sm mt-1">Positions will appear here when opened</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Symbol</TableHead>
            <TableHead>Direction</TableHead>
            <TableHead className="text-right">Size</TableHead>
            <TableHead className="text-right">Entry Price</TableHead>
            <TableHead className="text-right">Current Price</TableHead>
            <TableHead className="text-right">Unrealized P&L</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {positions.map((position, index) => {
            const isProfitable = position.unrealized_pnl >= 0;
            const priceChange = position.current_price - position.entry_price;
            const isLong = position.side === 'LONG';

            return (
              <TableRow
                key={position.position_id || index}
                className={cn(
                  "transition-colors",
                  isProfitable ? "hover:bg-green-50 dark:hover:bg-green-950/20" : "hover:bg-red-50 dark:hover:bg-red-950/20"
                )}
              >
                <TableCell className="font-medium">
                  {position.symbol}
                </TableCell>
                <TableCell>
                  <div className={cn(
                    "inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium",
                    isLong ? "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400" : "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400"
                  )}>
                    {isLong ? (
                      <ArrowUpIcon className="w-3 h-3" />
                    ) : (
                      <ArrowDownIcon className="w-3 h-3" />
                    )}
                    {position.side}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  {position.quantity}
                </TableCell>
                <TableCell className="text-right">
                  {formatCurrency(position.entry_price)}
                </TableCell>
                <TableCell className="text-right">
                  <div className="space-y-1">
                    <div>{formatCurrency(position.current_price)}</div>
                    <div className={cn(
                      "text-xs",
                      (isLong && priceChange > 0) || (!isLong && priceChange < 0)
                        ? "text-green-600"
                        : "text-red-600"
                    )}>
                      {priceChange > 0 ? '+' : ''}{priceChange.toFixed(2)}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className={cn(
                    "font-medium",
                    isProfitable ? "text-green-600" : "text-red-600"
                  )}>
                    {isProfitable ? '+' : ''}{formatCurrency(position.unrealized_pnl)}
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}