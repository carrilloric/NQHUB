/**
 * RiskMeters Component
 *
 * Displays risk gauges with color-coded indicators:
 * - <70%: Green
 * - 70-90%: Yellow (#f59e0b)
 * - >90%: Red (#ef4444)
 *
 * Metrics:
 * - Daily Loss (based on max_daily_loss threshold)
 * - Trailing Threshold (Apex compliance)
 */
import type { RiskCheckEvent } from '@/stores/websocketStore';

interface RiskMetersProps {
  riskStatus: RiskCheckEvent | null;
}

interface RiskMeterProps {
  label: string;
  value: number;
  threshold: number;
  format?: 'currency' | 'percentage';
}

function RiskMeter({ label, value, threshold, format = 'currency' }: RiskMeterProps) {
  // Calculate percentage used
  const percentage = Math.abs(value / threshold) * 100;

  // Determine color based on thresholds
  let color = 'bg-green-500';
  let textColor = 'text-green-600';

  if (percentage >= 90) {
    color = 'bg-red-500';
    textColor = 'text-red-600';
  } else if (percentage >= 70) {
    color = 'bg-yellow-500';
    textColor = 'text-yellow-600';
  }

  const displayValue =
    format === 'currency'
      ? `$${Math.abs(value).toFixed(2)}`
      : `${percentage.toFixed(1)}%`;

  return (
    <div className="flex flex-col gap-2" data-testid={`risk-meter-${label.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className={`text-lg font-bold ${textColor}`}>{displayValue}</span>
      </div>

      {/* Progress bar */}
      <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className={`h-full transition-all duration-300 ${color}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>

      <div className="flex justify-between text-xs text-gray-500">
        <span>0</span>
        <span>
          {format === 'currency' ? `$${threshold.toFixed(2)}` : '100%'}
        </span>
      </div>
    </div>
  );
}

export function RiskMeters({ riskStatus }: RiskMetersProps) {
  // Default risk config (Apex Trader Funding rules)
  const maxDailyLoss = 1000; // $1000 max daily loss
  const trailingThreshold = 2000; // $2000 trailing drawdown limit

  const dailyPnl = riskStatus?.current_pnl ?? 0;
  const accountBalance = riskStatus?.account_balance ?? 25000;

  // Calculate trailing drawdown (simplified)
  const trailingRemaining = Math.max(0, trailingThreshold - Math.abs(dailyPnl));

  return (
    <div className="rounded-lg border bg-white p-6">
      <h3 className="mb-4 text-lg font-semibold">Risk Metrics</h3>

      <div className="space-y-6">
        <RiskMeter
          label="Daily Loss"
          value={Math.abs(dailyPnl)}
          threshold={maxDailyLoss}
          format="currency"
        />

        <RiskMeter
          label="Trailing Threshold"
          value={Math.abs(dailyPnl)}
          threshold={trailingThreshold}
          format="currency"
        />

        {/* Account Balance */}
        <div className="mt-4 border-t pt-4">
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Account Balance:</span>
            <span className="text-sm font-semibold">${accountBalance.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
