/**
 * JournalEquityCurve - Equity curve chart using recharts
 * AUT-356
 */
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Trade } from '@/hooks/useTradeJournal';

interface JournalEquityCurveProps {
  trades: Trade[];
}

export function JournalEquityCurve({ trades }: JournalEquityCurveProps) {
  // Calculate cumulative P&L for equity curve
  const equityData = trades
    .sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime())
    .reduce((acc, trade, index) => {
      const prevEquity = index > 0 ? acc[index - 1].equity : 0;
      const newEquity = prevEquity + trade.net_pnl;

      acc.push({
        timestamp: new Date(trade.ts).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        }),
        equity: parseFloat(newEquity.toFixed(2)),
        pnl: trade.net_pnl,
      });

      return acc;
    }, [] as { timestamp: string; equity: number; pnl: number }[]);

  if (equityData.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow text-center text-gray-500 dark:text-gray-400">
        No data for equity curve
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Equity Curve
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={equityData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
          <XAxis
            dataKey="timestamp"
            tick={{ fill: 'currentColor' }}
            className="text-gray-600 dark:text-gray-400"
          />
          <YAxis
            tick={{ fill: 'currentColor' }}
            className="text-gray-600 dark:text-gray-400"
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Equity']}
          />
          <Line
            type="monotone"
            dataKey="equity"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ fill: '#2563eb', r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
