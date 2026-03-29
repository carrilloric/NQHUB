/**
 * Order Management Page
 * Shows all orders with status tracking and cancellation functionality
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Clock, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

// Types
interface Order {
  id: string;
  bot_id: string;
  bot_name: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  order_type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
  limit_price: number | null;
  stop_price: number | null;
  status: 'pending' | 'submitted' | 'filled' | 'cancelled' | 'rejected';
  filled_quantity: number;
  average_fill_price: number | null;
  created_at: string;
  updated_at: string;
  filled_at: string | null;
}

interface OrdersResponse {
  orders: Order[];
  total: number;
  offset: number;
  limit: number;
}

// API Functions
const fetchOrders = async (filters: {
  bot_id?: string;
  status?: string;
}): Promise<OrdersResponse> => {
  const params = new URLSearchParams();

  if (filters.bot_id) params.append('bot_id', filters.bot_id);
  if (filters.status) params.append('status', filters.status);

  const response = await fetch(`/api/v1/orders?${params}`);
  if (!response.ok) throw new Error('Failed to fetch orders');
  return response.json();
};

const fetchPendingOrders = async (): Promise<OrdersResponse> => {
  const response = await fetch('/api/v1/orders/pending');
  if (!response.ok) throw new Error('Failed to fetch pending orders');
  return response.json();
};

const fetchOrderDetails = async (orderId: string): Promise<Order> => {
  const response = await fetch(`/api/v1/orders/${orderId}`);
  if (!response.ok) throw new Error('Failed to fetch order details');
  return response.json();
};

const cancelOrder = async (orderId: string): Promise<any> => {
  const response = await fetch(`/api/v1/orders/${orderId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to cancel order');
  }
  return response.json();
};

// Helper Components
const StatusBadge = ({ status }: { status: string }) => {
  const variants: Record<string, { color: string; label: string }> = {
    pending: { color: 'bg-yellow-600', label: 'Pending' },
    submitted: { color: 'bg-blue-600', label: 'Submitted' },
    filled: { color: 'bg-green-600', label: 'Filled' },
    cancelled: { color: 'bg-gray-600', label: 'Cancelled' },
    rejected: { color: 'bg-red-600', label: 'Rejected' },
  };

  const variant = variants[status] || variants.pending;

  return (
    <Badge className={cn('uppercase', variant.color)}>
      {variant.label}
    </Badge>
  );
};

const SideBadge = ({ side }: { side: string }) => (
  <Badge
    variant={side === 'BUY' ? 'default' : 'secondary'}
    className={cn(
      'uppercase',
      side === 'BUY' && 'bg-green-600 hover:bg-green-700',
      side === 'SELL' && 'bg-red-600 hover:bg-red-700'
    )}
  >
    {side}
  </Badge>
);

const TimeElapsed = ({ createdAt }: { createdAt: string }) => {
  const [elapsed, setElapsed] = useState('');

  useEffect(() => {
    const updateElapsed = () => {
      const now = new Date().getTime();
      const created = new Date(createdAt).getTime();
      const diff = now - created;

      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);

      if (hours > 0) {
        setElapsed(`${hours}h ${minutes % 60}m ago`);
      } else if (minutes > 0) {
        setElapsed(`${minutes}m ${seconds % 60}s ago`);
      } else {
        setElapsed(`${seconds}s ago`);
      }
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);

    return () => clearInterval(interval);
  }, [createdAt]);

  return (
    <span className="text-xs text-muted-foreground flex items-center gap-1">
      <Clock className="h-3 w-3" />
      {elapsed}
    </span>
  );
};

// Pending Orders Panel
const PendingOrdersPanel = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [orderToCancel, setOrderToCancel] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['pendingOrders'],
    queryFn: fetchPendingOrders,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  const cancelMutation = useMutation({
    mutationFn: cancelOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingOrders'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      toast({
        title: 'Order Cancelled',
        description: 'The order has been cancelled successfully.',
      });
      setCancelDialogOpen(false);
      setOrderToCancel(null);
    },
    onError: (error: Error) => {
      toast({
        title: 'Cancel Failed',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const handleCancelClick = (orderId: string) => {
    setOrderToCancel(orderId);
    setCancelDialogOpen(true);
  };

  const handleConfirmCancel = () => {
    if (orderToCancel) {
      cancelMutation.mutate(orderToCancel);
    }
  };

  const pendingOrders = data?.orders || [];

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Pending Orders</span>
            <Badge variant="outline">Auto-refresh: 5s</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading pending orders...
            </div>
          ) : pendingOrders.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No pending orders
            </div>
          ) : (
            <div className="space-y-3">
              {pendingOrders.map((order) => (
                <div
                  key={order.id}
                  className="flex items-center justify-between p-3 border rounded-md bg-yellow-50 dark:bg-yellow-950"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <SideBadge side={order.side} />
                      <span className="font-mono text-sm">{order.symbol}</span>
                      <span className="text-sm">×{order.quantity}</span>
                      <span className="text-xs text-muted-foreground">
                        {order.order_type}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {order.bot_name}
                      {order.limit_price && (
                        <span className="ml-2">
                          @ ${order.limit_price.toFixed(2)}
                        </span>
                      )}
                    </div>
                    <TimeElapsed createdAt={order.created_at} />
                  </div>
                  <Button
                    onClick={() => handleCancelClick(order.id)}
                    variant="destructive"
                    size="sm"
                    disabled={cancelMutation.isPending}
                  >
                    <X className="h-4 w-4 mr-1" />
                    Cancel
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Order?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel this pending order? This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmCancel}>
              Confirm Cancel
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

// Order Detail Sheet
const OrderDetailSheet = ({
  orderId,
  open,
  onClose,
}: {
  orderId: string | null;
  open: boolean;
  onClose: () => void;
}) => {
  const { data: order } = useQuery({
    queryKey: ['order', orderId],
    queryFn: () => fetchOrderDetails(orderId!),
    enabled: !!orderId && open,
  });

  if (!order) return null;

  const slippage =
    order.average_fill_price && order.limit_price
      ? Math.abs(order.average_fill_price - order.limit_price)
      : null;

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-[500px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Order Details</SheetTitle>
          <SheetDescription>
            {order.symbol} {order.side} • {order.bot_name}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Status */}
          <div>
            <Label className="text-xs text-muted-foreground">Status</Label>
            <div className="mt-1">
              <StatusBadge status={order.status} />
            </div>
          </div>

          {/* Order Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-xs text-muted-foreground">Side</Label>
              <div className="mt-1">
                <SideBadge side={order.side} />
              </div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Order Type</Label>
              <div className="font-mono">{order.order_type}</div>
            </div>
          </div>

          {/* Quantity */}
          <div>
            <Label className="text-xs text-muted-foreground">Quantity</Label>
            <div className="text-lg font-semibold">
              {order.quantity} contracts
            </div>
            {order.filled_quantity > 0 && (
              <div className="text-sm text-muted-foreground">
                {order.filled_quantity} filled
              </div>
            )}
          </div>

          {/* Prices */}
          <div className="grid grid-cols-2 gap-4">
            {order.limit_price && (
              <div>
                <Label className="text-xs text-muted-foreground">
                  Limit Price
                </Label>
                <div className="font-mono text-lg">
                  ${order.limit_price.toFixed(2)}
                </div>
              </div>
            )}
            {order.stop_price && (
              <div>
                <Label className="text-xs text-muted-foreground">
                  Stop Price
                </Label>
                <div className="font-mono text-lg">
                  ${order.stop_price.toFixed(2)}
                </div>
              </div>
            )}
          </div>

          {/* Fill Details (if filled) */}
          {order.status === 'filled' && order.average_fill_price && (
            <div className="border-t pt-4">
              <Label className="text-sm font-semibold">Fill Details</Label>
              <div className="mt-3 space-y-3">
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Average Fill Price
                  </Label>
                  <div className="font-mono text-lg">
                    ${order.average_fill_price.toFixed(2)}
                  </div>
                </div>
                {slippage !== null && order.limit_price && (
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Slippage
                    </Label>
                    <div
                      className={cn(
                        'font-mono',
                        slippage > 0 ? 'text-red-600' : 'text-green-600'
                      )}
                    >
                      ${slippage.toFixed(2)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {((slippage / order.limit_price) * 100).toFixed(3)}% of
                      limit price
                    </div>
                  </div>
                )}
                {order.filled_at && (
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Filled At
                    </Label>
                    <div className="text-sm">
                      {new Date(order.filled_at).toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Timestamps */}
          <div className="border-t pt-4">
            <Label className="text-sm font-semibold">Timestamps</Label>
            <div className="mt-3 space-y-2 text-sm">
              <div>
                <Label className="text-xs text-muted-foreground">Created</Label>
                <div>{new Date(order.created_at).toLocaleString()}</div>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Updated</Label>
                <div>{new Date(order.updated_at).toLocaleString()}</div>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

// Main Component
export default function OrderManagement() {
  const [filters, setFilters] = useState<{ status?: string }>({});
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['orders', filters],
    queryFn: () => fetchOrders(filters),
  });

  const orders = data?.orders || [];

  const handleOrderClick = (orderId: string) => {
    setSelectedOrderId(orderId);
    setSheetOpen(true);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Order Management</h1>
        <p className="text-muted-foreground">
          Monitor and manage all trading orders
        </p>
      </div>

      {/* Pending Orders Panel */}
      <PendingOrdersPanel />

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="w-[200px]">
              <Label>Status</Label>
              <Select
                value={filters.status || 'all'}
                onValueChange={(value) =>
                  setFilters((prev) => ({
                    ...prev,
                    status: value === 'all' ? undefined : value,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="filled">Filled</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button onClick={() => setFilters({})} variant="outline">
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {orders.length} order{orders.length !== 1 ? 's' : ''} found
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading orders...
            </div>
          ) : orders.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No orders found. Start trading to see orders here!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Bot</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Fill Price</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((order) => (
                    <TableRow
                      key={order.id}
                      onClick={() => handleOrderClick(order.id)}
                      className="cursor-pointer hover:bg-muted/50"
                    >
                      <TableCell className="text-sm">
                        {new Date(order.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-sm">{order.bot_name}</TableCell>
                      <TableCell className="font-mono text-xs">
                        {order.order_type}
                      </TableCell>
                      <TableCell>
                        <SideBadge side={order.side} />
                      </TableCell>
                      <TableCell className="font-mono">{order.symbol}</TableCell>
                      <TableCell>{order.quantity}</TableCell>
                      <TableCell className="font-mono text-sm">
                        {order.limit_price
                          ? `$${order.limit_price.toFixed(2)}`
                          : 'MARKET'}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={order.status} />
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {order.average_fill_price
                          ? `$${order.average_fill_price.toFixed(2)}`
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Order Detail Sheet */}
      <OrderDetailSheet
        orderId={selectedOrderId}
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
      />
    </div>
  );
}
