/**
 * PnLSummary - Summary statistics for trades
 * AUT-356
 */
import { TradeSummary } from '@/hooks/useTradeJournal';

interface PnLSummaryProps {
  summary: TradeSummary;
}

export function PnLSummary({ summary }: PnLSummaryProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div className="text-sm text-gray-600 dark:text-gray-400">Total P&L</div>
        <div className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatCurrency(summary.total_pnl)}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div className="text-sm text-gray-600 dark:text-gray-400">Total Trades</div>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {summary.total_trades}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div className="text-sm text-gray-600 dark:text-gray-400">Win Rate</div>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatPercent(summary.win_rate)}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div className="text-sm text-gray-600 dark:text-gray-400">Profit Factor</div>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {summary.profit_factor.toFixed(2)}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div className="text-sm text-gray-600 dark:text-gray-400">W/L</div>
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {summary.wins}/{summary.losses}
        </div>
      </div>
    </div>
  );
}
