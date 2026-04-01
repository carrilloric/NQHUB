/**
 * GlobalKillSwitchBar Component
 *
 * Prominent red bar always visible at the top of Risk Monitor page.
 * Provides "KILL ALL BOTS" emergency button.
 *
 * Features:
 * - Always visible (cannot be hidden)
 * - Dark red background for high visibility
 * - Requires reason in modal before killing all bots
 * - POST /api/v1/bots/kill-all
 */
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface GlobalKillSwitchBarProps {
  /** Callback when kill all is confirmed */
  onKillAll: (reason: string) => Promise<void>;

  /** Whether kill operation is in progress */
  isLoading?: boolean;
}

export function GlobalKillSwitchBar({ onKillAll, isLoading = false }: GlobalKillSwitchBarProps) {
  const [showModal, setShowModal] = useState(false);
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleKillAll = async () => {
    if (!reason.trim()) {
      setError('Reason is required');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await onKillAll(reason);
      setShowModal(false);
      setReason('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to kill all bots');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setShowModal(false);
    setReason('');
    setError(null);
  };

  return (
    <>
      {/* Red alert bar - always visible */}
      <div className="bg-red-900 border-b-4 border-red-700 px-6 py-4 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h2 className="text-white font-bold text-lg">Global Kill Switch</h2>
              <p className="text-red-200 text-sm">
                Emergency shutdown for all trading bots
              </p>
            </div>
          </div>

          <Button
            onClick={() => setShowModal(true)}
            disabled={isLoading}
            variant="destructive"
            size="lg"
            className="bg-red-600 hover:bg-red-500 text-white font-bold px-8 py-6 text-lg shadow-xl transition-all hover:scale-105"
          >
            🛑 KILL ALL BOTS
          </Button>
        </div>
      </div>

      {/* Confirmation Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-red-600 flex items-center space-x-2">
              <span className="text-2xl">⚠️</span>
              <span>Kill All Bots</span>
            </DialogTitle>
            <DialogDescription>
              This will immediately stop all trading bots, close all open positions,
              and cancel all pending orders. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reason" className="text-sm font-semibold">
                Reason (Required) <span className="text-red-500">*</span>
              </Label>
              <Input
                id="reason"
                placeholder="e.g., Daily loss limit exceeded, market volatility, manual intervention..."
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  setError(null);
                }}
                disabled={isSubmitting}
                className={error ? 'border-red-500' : ''}
              />
              {error && <p className="text-sm text-red-600">{error}</p>}
            </div>

            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-3">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <strong>Warning:</strong> All bots will be killed immediately after
                confirmation. Open positions will be closed at market price.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleKillAll}
              disabled={isSubmitting || !reason.trim()}
              className="bg-red-600 hover:bg-red-500"
            >
              {isSubmitting ? 'Killing...' : 'Confirm Kill All'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
