/**
 * TradeJournal - Trade Journal & Order Management Page
 * AUT-356
 */
import { useState } from 'react';
import { useTradeJournal, type TradeFilters, type Trade } from '@/hooks/useTradeJournal';
import { useOrderManagement, type Order } from '@/hooks/useOrderManagement';
import { TradeFilterBar } from '@/components/journal/TradeFilterBar';
import { PnLSummary } from '@/components/journal/PnLSummary';
import { TradeListTable } from '@/components/journal/TradeListTable';
import { JournalEquityCurve } from '@/components/journal/JournalEquityCurve';
import { NotesEditor } from '@/components/journal/NotesEditor';
import { ActiveOrdersTable } from '@/components/journal/OrderManagement/ActiveOrdersTable';
import { OrderDetailPanel } from '@/components/journal/OrderManagement/OrderDetailPanel';
import { FilledOrdersTable } from '@/components/journal/OrderManagement/FilledOrdersTable';

type TabType = 'journal' | 'orders';

export default function TradeJournal() {
  const [activeTab, setActiveTab] = useState<TabType>('journal');
  const [filters, setFilters] = useState<TradeFilters>({ direction: 'ALL' });
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  // Trade Journal hook
  const { trades, summary, isLoading: tradesLoading, updateNotes } = useTradeJournal(filters);

  // Order Management hook
  const {
    pendingOrders,
    filledOrders,
    isLoading: ordersLoading,
    cancelOrder,
  } = useOrderManagement();

  const handleFilterChange = (newFilters: TradeFilters) => {
    setFilters(newFilters);
  };

  const handleSelectTrade = (trade: Trade) => {
    setSelectedTrade(trade);
  };

  const handleSelectOrder = (order: Order) => {
    setSelectedOrder(order);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          Trade Journal & Order Management
        </h1>

        {/* Tab Navigation */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex">
              <button
                onClick={() => setActiveTab('journal')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'journal'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Trade Journal
              </button>
              <button
                onClick={() => setActiveTab('orders')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'orders'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Order Management
              </button>
            </nav>
          </div>
        </div>

        {/* Tab 1: Trade Journal */}
        {activeTab === 'journal' && (
          <div className="space-y-6">
            <TradeFilterBar onFilterChange={handleFilterChange} />

            {tradesLoading ? (
              <div className="text-center text-gray-500 dark:text-gray-400">Loading trades...</div>
            ) : (
              <>
                <PnLSummary summary={summary} />

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <TradeListTable
                      trades={trades}
                      onSelectTrade={handleSelectTrade}
                      selectedTradeId={selectedTrade?.id}
                    />
                  </div>
                  <div className="space-y-6">
                    <JournalEquityCurve trades={trades} />
                    <NotesEditor
                      tradeId={selectedTrade?.id}
                      initialNotes={selectedTrade?.notes}
                      initialTags={selectedTrade?.tags}
                      onSave={updateNotes}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab 2: Order Management */}
        {activeTab === 'orders' && (
          <div className="space-y-6">
            {ordersLoading ? (
              <div className="text-center text-gray-500 dark:text-gray-400">Loading orders...</div>
            ) : (
              <>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Active Orders
                  </h2>
                  <ActiveOrdersTable
                    orders={pendingOrders}
                    onCancel={cancelOrder}
                    onSelectOrder={handleSelectOrder}
                    selectedOrderId={selectedOrder?.id}
                  />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      Filled Orders
                    </h2>
                    <FilledOrdersTable orders={filledOrders} />
                  </div>
                  <div>
                    <OrderDetailPanel
                      order={selectedOrder}
                      relatedOrders={[...pendingOrders, ...filledOrders]}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
