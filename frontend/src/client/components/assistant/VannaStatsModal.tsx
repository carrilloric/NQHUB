import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Loader2, Download, RefreshCw, Database, TrendingUp } from 'lucide-react';
import { assistantApi } from '@/assistant/services/assistantApi';
import type { VannaStats } from '@/assistant/types';
import { useToast } from '@/components/ui/use-toast';

interface VannaStatsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const VannaStatsModal: React.FC<VannaStatsModalProps> = ({ open, onOpenChange }) => {
  const { toast } = useToast();
  const [stats, setStats] = useState<VannaStats | null>(null);
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await assistantApi.getVannaStats();
      setStats(data);
    } catch (error: any) {
      toast({ title: 'Error', description: error.message, variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const data = await assistantApi.exportVannaData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vanna-training-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast({ title: 'Success', description: 'Training data exported successfully' });
    } catch (error: any) {
      toast({ title: 'Error', description: error.message, variant: 'destructive' });
    }
  };

  useEffect(() => {
    if (open) loadStats();
  }, [open]);

  if (!stats || stats.status === 'unavailable') {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Database className="size-5" />
              Vanna.AI Learning Statistics
            </DialogTitle>
          </DialogHeader>
          <div className="text-center py-8 text-muted-foreground">
            {loading ? (
              <Loader2 className="size-8 animate-spin mx-auto mb-2" />
            ) : (
              <p>Vanna not initialized yet. Send your first query to start learning!</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="size-5" />
            Vanna.AI Learning Statistics
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="general" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="general">General Stats</TabsTrigger>
            <TabsTrigger value="breakdown">Category Breakdown</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <StatCard label="Total Examples" value={stats.total_documents} />
              <StatCard label="SQL Queries" value={stats.total_sql_examples} />
              <StatCard label="DDL Schemas" value={stats.total_ddl} />
              <StatCard label="Status" value={stats.status} variant="success" />
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-sm">Collections</h3>
              {stats.collections?.map((col) => (
                <div key={col.name} className="flex justify-between p-2 bg-muted rounded">
                  <span className="text-sm">{col.name}</span>
                  <span className="text-sm font-mono">{col.count}</span>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="breakdown" className="space-y-4">
            {stats.breakdown && (
              <div className="space-y-3">
                <CategoryBar label="FVGs" count={stats.breakdown.fvg} total={stats.total_sql_examples} />
                <CategoryBar label="Liquidity Pools" count={stats.breakdown.liquidity_pools} total={stats.total_sql_examples} />
                <CategoryBar label="Order Blocks" count={stats.breakdown.order_blocks} total={stats.total_sql_examples} />
                <CategoryBar label="ETL Jobs" count={stats.breakdown.etl} total={stats.total_sql_examples} />
                <CategoryBar label="Candles" count={stats.breakdown.candles} total={stats.total_sql_examples} />
                <CategoryBar label="Other" count={stats.breakdown.other} total={stats.total_sql_examples} />
              </div>
            )}
          </TabsContent>
        </Tabs>

        <div className="flex gap-2 justify-end pt-4 border-t">
          <Button variant="outline" size="sm" onClick={loadStats} disabled={loading}>
            <RefreshCw className="size-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="size-4 mr-2" />
            Export JSON
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const StatCard: React.FC<{ label: string; value: string | number; variant?: 'default' | 'success' }> = ({ label, value, variant = 'default' }) => (
  <div className="p-4 bg-muted rounded-lg">
    <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
    <p className={`text-2xl font-bold mt-1 ${variant === 'success' ? 'text-green-500' : ''}`}>{value}</p>
  </div>
);

const CategoryBar: React.FC<{ label: string; count: number; total: number }> = ({ label, count, total }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-muted-foreground">{count} queries</span>
      </div>
      <div className="w-full bg-muted rounded-full h-2">
        <div className="bg-primary h-2 rounded-full transition-all" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
};
