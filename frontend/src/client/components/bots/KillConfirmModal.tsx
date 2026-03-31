/**
 * KillConfirmModal Component (AUT-354)
 *
 * Emergency kill switch modal for stopping bots immediately.
 * Confirm button is DISABLED until reason field has text.
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertTriangle } from 'lucide-react';

interface KillConfirmModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  botName: string;
  onConfirm: (reason: string) => void;
  isLoading?: boolean;
}

export function KillConfirmModal({
  open,
  onOpenChange,
  botName,
  onConfirm,
  isLoading = false,
}: KillConfirmModalProps) {
  const [reason, setReason] = useState('');

  const handleConfirm = () => {
    if (reason.trim()) {
      onConfirm(reason.trim());
      setReason(''); // Reset after confirm
    }
  };

  const handleCancel = () => {
    setReason(''); // Reset on cancel
    onOpenChange(false);
  };

  // AUT-354 spec: confirm button disabled until reason has text
  const isConfirmDisabled = !reason.trim() || isLoading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-500" />
            </div>
            <div>
              <DialogTitle>Kill Bot: {botName}</DialogTitle>
              <DialogDescription className="mt-1">
                This will immediately halt the bot and close all positions
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="kill-reason" className="text-sm font-medium">
              Reason for Emergency Stop <span className="text-red-500">*</span>
            </Label>
            <Input
              id="kill-reason"
              placeholder="e.g., Margin call, unexpected behavior, risk limit breach..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={isLoading}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !isConfirmDisabled) {
                  handleConfirm();
                }
              }}
            />
            <p className="text-xs text-muted-foreground">
              This reason will be logged in the bot's state transition history
            </p>
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900/50 dark:bg-amber-900/10">
            <p className="text-sm text-amber-900 dark:text-amber-200">
              <strong>Warning:</strong> Kill switch will:
            </p>
            <ul className="mt-2 space-y-1 text-sm text-amber-800 dark:text-amber-300">
              <li>• Close all open positions immediately</li>
              <li>• Cancel all pending orders</li>
              <li>• Set bot status to HALTED</li>
              <li>• Require manual resume to restart</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            disabled={isConfirmDisabled}
          >
            {isLoading ? 'Killing Bot...' : 'Confirm Kill'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
