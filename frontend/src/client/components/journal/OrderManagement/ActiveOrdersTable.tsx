/**
 * ActiveOrdersTable - Table of active/pending orders
 * AUT-356
 */
import { Order } from '@/hooks/useOrderManagement';

interface ActiveOrdersTableProps {
  orders: Order[];
  onCancel: (orderId: string) => Promise<boolean>;
  onSelectOrder: (order: Order) => void;
  selectedOrderId?: string;
}

export function ActiveOrdersTable({ orders, onCancel, onSelectOrder, selectedOrderId }: ActiveOrdersTableProps) {
  const handleCancel = async (e: React.MouseEvent, orderId: string) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to cancel this order?')) {
      await onCancel(orderId);
    }
  };

  const canCancelOrder = (status: string) => {
    return status === 'PENDING_SUBMIT' || status === 'SUBMITTED';
  };

  if (orders.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow text-center text-gray-500 dark:text-gray-400">
        No active orders
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Order ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Side
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Contracts
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Limit Price
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {orders.map((order) => (
              <tr
                key={order.id}
                onClick={() => onSelectOrder(order)}
                className={`cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${
                  selectedOrderId === order.id ? 'bg-blue-50 dark:bg-blue-900' : ''
                }`}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {order.id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {order.order_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      order.bracket_role === 'ENTRY'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : order.bracket_role === 'TP'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : order.bracket_role === 'SL'
                        ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}
                  >
                    {order.bracket_role || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {order.side}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
                  {order.contracts}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
                  {order.limit_price?.toFixed(2) || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      order.status === 'PENDING_SUBMIT'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        : order.status === 'SUBMITTED'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}
                  >
                    {order.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {canCancelOrder(order.status) && (
                    <button
                      onClick={(e) => handleCancel(e, order.id)}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-medium"
                    >
                      Cancel
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
