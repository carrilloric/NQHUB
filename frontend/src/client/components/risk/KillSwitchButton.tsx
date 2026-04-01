/**
 * KillSwitchButton Component
 *
 * Button to kill a specific bot with confirmation modal.
 * Requires reason before killing.
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

interface KillSwitchButtonProps {
  /** Bot ID to kill */
  botId: string;

  /** Bot name for display */
  botName: string;

  /** Callback when kill is confirmed */
  onKill: (botId: string, reason: string) => Promise<void>;

  /** Optional className */
  className?: string;
}

export function KillSwitchButton({
  botId,
  botName,
  onKill,
  className,
}: KillSwitchButtonProps) {
  const [showModal, setShowModal] = useState(false);
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleKill = async () => {
    if (!reason.trim()) {
      setError('Reason is required');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await onKill(botId, reason);
      setShowModal(false);
      setReason('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to kill bot');
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
      <Button
        onClick={() => setShowModal(true)}
        variant="destructive"
        size="sm"
        className={className}
      >
        🛑 Kill Bot
      </Button>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-red-600">Kill Bot: {botName}</DialogTitle>
            <DialogDescription>
              This will stop the bot and close all positions. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="bot-kill-reason">
                Reason (Required) <span className="text-red-500">*</span>
              </Label>
              <Input
                id="bot-kill-reason"
                placeholder="Enter reason for killing this bot..."
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
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancel} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleKill}
              disabled={isSubmitting || !reason.trim()}
            >
              {isSubmitting ? 'Killing...' : 'Confirm Kill'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
