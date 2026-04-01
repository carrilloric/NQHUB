/**
 * OpenPositions Component
 *
 * Displays open trading positions in a table format.
 * Updates in real-time via WebSocket (positions channel).
 */
import type { PositionEvent } from '@/stores/websocketStore';

interface OpenPositionsProps {
  positions: PositionEvent[];
}

export function OpenPositions({ positions }: OpenPositionsProps) {
  if (positions.length === 0) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold">Open Positions</h3>
        <p className="text-center text-gray-500">No open positions</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-6">
      <h3 className="mb-4 text-lg font-semibold">Open Positions</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" data-testid="positions-table">
          <thead>
            <tr className="border-b text-left text-gray-600">
              <th className="pb-2">Symbol</th>
              <th className="pb-2">Side</th>
              <th className="pb-2">Qty</th>
              <th className="pb-2">Entry</th>
              <th className="pb-2">Current</th>
              <th className="pb-2">P&L</th>
              <th className="pb-2">Ticks</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position, idx) => {
              const pnlColor = position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600';
              const sideColor = position.side === 'LONG' ? 'text-blue-600' : 'text-orange-600';

              return (
                <tr key={idx} className="border-b last:border-0">
                  <td className="py-2 font-medium">{position.symbol}</td>
                  <td className={`py-2 font-medium ${sideColor}`}>{position.side}</td>
                  <td className="py-2">{position.contracts}</td>
                  <td className="py-2">${position.entry_price.toFixed(2)}</td>
                  <td className="py-2">${position.current_price.toFixed(2)}</td>
                  <td className={`py-2 font-semibold ${pnlColor}`}>
                    ${position.unrealized_pnl.toFixed(2)}
                  </td>
                  <td className={`py-2 ${pnlColor}`}>
                    {position.unrealized_pnl_ticks.toFixed(1)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
