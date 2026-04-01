/**
 * Hook for Order Management data management
 * AUT-356
 */
import { useState, useEffect } from 'react';

export interface Order {
  id: string;
  bot_id: string;
  order_type: string;
  bracket_role?: 'ENTRY' | 'TP' | 'SL';
  side: 'BUY' | 'SELL';
  contracts: number;
  limit_price?: number;
  fill_price?: number;
  status: 'PENDING_SUBMIT' | 'SUBMITTED' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  submitted_at: string;
  filled_at?: string;
}

export function useOrderManagement() {
  const [pendingOrders, setPendingOrders] = useState<Order[]>([]);
  const [filledOrders, setFilledOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch pending orders
      const pendingResponse = await fetch('/api/v1/orders/pending');
      if (!pendingResponse.ok) {
        throw new Error('Failed to fetch pending orders');
      }
      const pendingData = await pendingResponse.json();
      setPendingOrders(pendingData.orders);

      // Fetch filled orders
      const filledResponse = await fetch('/api/v1/orders?status=FILLED');
      if (!filledResponse.ok) {
        throw new Error('Failed to fetch filled orders');
      }
      const filledData = await filledResponse.json();
      setFilledOrders(filledData.orders);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const cancelOrder = async (orderId: string) => {
    try {
      const response = await fetch(`/api/v1/orders/${orderId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to cancel order');
      }

      // Remove from local state
      setPendingOrders(prev => prev.filter(o => o.id !== orderId));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    }
  };

  return {
    pendingOrders,
    filledOrders,
    isLoading,
    error,
    cancelOrder,
    refetch: fetchOrders,
  };
}
