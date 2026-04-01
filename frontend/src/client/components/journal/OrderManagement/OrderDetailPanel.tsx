/**
 * OrderDetailPanel - Detailed view of order with bracket legs
 * AUT-356
 */
import { Order } from '@/hooks/useOrderManagement';

interface OrderDetailPanelProps {
  order: Order | null;
  relatedOrders?: Order[];
}

export function OrderDetailPanel({ order, relatedOrders = [] }: OrderDetailPanelProps) {
  if (!order) {
    return (
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow text-center text-gray-500 dark:text-gray-400">
        Select an order to view details
      </div>
    );
  }

  // Find bracket legs (ENTRY, TP, SL) by bot_id
  const bracketLegs = relatedOrders.filter((o) => o.bot_id === order.bot_id);
  const entryOrder = bracketLegs.find((o) => o.bracket_role === 'ENTRY');
  const tpOrder = bracketLegs.find((o) => o.bracket_role === 'TP');
  const slOrder = bracketLegs.find((o) => o.bracket_role === 'SL');

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Order Details
      </h3>

      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Order ID:</span>
            <p className="font-medium text-gray-900 dark:text-gray-100">{order.id}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Bot ID:</span>
            <p className="font-medium text-gray-900 dark:text-gray-100">{order.bot_id}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Type:</span>
            <p className="font-medium text-gray-900 dark:text-gray-100">{order.order_type}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Side:</span>
            <p className="font-medium text-gray-900 dark:text-gray-100">{order.side}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Contracts:</span>
            <p className="font-medium text-gray-900 dark:text-gray-100">{order.contracts}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Status:</span>
            <p className="font-medium text-gray-900 dark:text-gray-100">{order.status}</p>
          </div>
        </div>

        {bracketLegs.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Bracket Orders
            </h4>
            <div className="space-y-2">
              {entryOrder && (
                <div className="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900 rounded">
                  <div>
                    <span className="text-xs font-medium text-blue-800 dark:text-blue-200">ENTRY</span>
                    <p className="text-sm text-gray-900 dark:text-gray-100 mt-1">{entryOrder.id}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-gray-600 dark:text-gray-400">Limit Price</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {entryOrder.limit_price?.toFixed(2)}
                    </p>
                  </div>
                </div>
              )}
              {tpOrder && (
                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900 rounded">
                  <div>
                    <span className="text-xs font-medium text-green-800 dark:text-green-200">TAKE PROFIT</span>
                    <p className="text-sm text-gray-900 dark:text-gray-100 mt-1">{tpOrder.id}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-gray-600 dark:text-gray-400">Limit Price</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {tpOrder.limit_price?.toFixed(2)}
                    </p>
                  </div>
                </div>
              )}
              {slOrder && (
                <div className="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900 rounded">
                  <div>
                    <span className="text-xs font-medium text-red-800 dark:text-red-200">STOP LOSS</span>
                    <p className="text-sm text-gray-900 dark:text-gray-100 mt-1">{slOrder.id}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-gray-600 dark:text-gray-400">Limit Price</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {slOrder.limit_price?.toFixed(2)}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
