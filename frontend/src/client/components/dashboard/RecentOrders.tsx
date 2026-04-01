/**
 * RecentOrders Component
 *
 * Displays the last 10 orders received via WebSocket (orders channel).
 * Shows order ID, side, contracts, status, and fill price.
 */
import type { OrderEvent } from '@/stores/websocketStore';

interface RecentOrdersProps {
  orders: OrderEvent[];
}

export function RecentOrders({ orders }: RecentOrdersProps) {
  if (orders.length === 0) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold">Recent Orders</h3>
        <p className="text-center text-gray-500">No recent orders</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-6">
      <h3 className="mb-4 text-lg font-semibold">Recent Orders (Last 10)</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" data-testid="orders-table">
          <thead>
            <tr className="border-b text-left text-gray-600">
              <th className="pb-2">ID</th>
              <th className="pb-2">Side</th>
              <th className="pb-2">Qty</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Fill Price</th>
            </tr>
          </thead>
          <tbody>
            {orders.slice(0, 10).map((order, idx) => {
              const sideColor = order.side === 'BUY' ? 'text-green-600' : 'text-red-600';

              let statusColor = 'text-gray-600';
              if (order.status === 'FILLED') statusColor = 'text-green-600';
              if (order.status === 'REJECTED') statusColor = 'text-red-600';
              if (order.status === 'CANCELLED') statusColor = 'text-orange-600';

              return (
                <tr key={idx} className="border-b last:border-0">
                  <td className="py-2 font-mono text-xs">{order.client_order_id.slice(-8)}</td>
                  <td className={`py-2 font-medium ${sideColor}`}>{order.side}</td>
                  <td className="py-2">{order.contracts}</td>
                  <td className={`py-2 font-medium ${statusColor}`}>{order.status}</td>
                  <td className="py-2">
                    {order.fill_price ? `$${order.fill_price.toFixed(2)}` : '-'}
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
