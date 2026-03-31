import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ApexCompliance } from '@/hooks/useBacktest';

interface ApexComplianceCardProps {
  compliance: ApexCompliance | null;
  className?: string;
}

export function ApexComplianceCard({ compliance, className }: ApexComplianceCardProps) {
  if (!compliance) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle>Apex Compliance</CardTitle>
          <CardDescription>No compliance data available</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const isCompliant = compliance.compliant;
  const complianceColor = isCompliant ? '#22c55e' : '#ef4444';

  return (
    <Card
      className={cn('w-full', className)}
      data-testid="apex-compliance-card"
    >
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Apex Compliance</CardTitle>
            <CardDescription>Evaluation against Apex funding rules</CardDescription>
          </div>
          <div
            className={cn(
              'flex items-center gap-2 text-lg font-semibold px-3 py-1 rounded-md',
              isCompliant ? 'text-[#22c55e] bg-[#22c55e]/10' : 'text-[#ef4444] bg-[#ef4444]/10'
            )}
            style={{ color: complianceColor }}
          >
            {isCompliant ? (
              <>
                <CheckCircle2 className="h-5 w-5" />
                PASS
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5" />
                FAIL
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Trailing Threshold */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            {compliance.trailing_threshold.passed ? (
              <CheckCircle2 className="h-4 w-4 text-[#22c55e]" />
            ) : (
              <XCircle className="h-4 w-4 text-[#ef4444]" />
            )}
            <span className="font-medium">Trailing Threshold</span>
          </div>
          <div className="text-right">
            <div className={cn(
              'font-mono text-sm',
              compliance.trailing_threshold.passed ? 'text-[#22c55e]' : 'text-[#ef4444]'
            )}>
              ${Math.abs(compliance.trailing_threshold.value).toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">
              Max: ${Math.abs(compliance.trailing_threshold.max_allowed).toLocaleString()}
            </div>
          </div>
        </div>

        {/* Max Contracts */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            {compliance.max_contracts.passed ? (
              <CheckCircle2 className="h-4 w-4 text-[#22c55e]" />
            ) : (
              <XCircle className="h-4 w-4 text-[#ef4444]" />
            )}
            <span className="font-medium">Max Contracts</span>
          </div>
          <div className="text-right">
            <div className={cn(
              'font-mono text-sm',
              compliance.max_contracts.passed ? 'text-[#22c55e]' : 'text-[#ef4444]'
            )}>
              {compliance.max_contracts.value} contracts
            </div>
            <div className="text-xs text-muted-foreground">
              Limit: {compliance.max_contracts.max_allowed} contracts
            </div>
          </div>
        </div>

        {/* Trading Hours */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            {compliance.trading_hours.compliant ? (
              <CheckCircle2 className="h-4 w-4 text-[#22c55e]" />
            ) : (
              <XCircle className="h-4 w-4 text-[#ef4444]" />
            )}
            <span className="font-medium">Trading Hours</span>
          </div>
          <div className="text-right">
            {compliance.trading_hours.compliant ? (
              <div className="text-sm text-[#22c55e]">Compliant</div>
            ) : (
              <div>
                <div className="text-sm text-[#ef4444]">Violations Found</div>
                {compliance.trading_hours.violations.length > 0 && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {compliance.trading_hours.violations.length} violation(s)
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Profit Goal */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            {compliance.profit_goal.passed ? (
              <CheckCircle2 className="h-4 w-4 text-[#22c55e]" />
            ) : (
              <AlertCircle className="h-4 w-4 text-yellow-600" />
            )}
            <span className="font-medium">Profit Goal</span>
          </div>
          <div className="text-right">
            <div className={cn(
              'font-mono text-sm',
              compliance.profit_goal.passed ? 'text-[#22c55e]' : 'text-yellow-600'
            )}>
              ${compliance.profit_goal.value.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">
              Target: ${compliance.profit_goal.target.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Overall Status Message */}
        {!isCompliant && compliance.trading_hours.violations.length > 0 && (
          <div className="mt-3 p-3 bg-[#ef4444]/10 border border-[#ef4444]/20 rounded-lg">
            <div className="text-sm font-medium text-[#ef4444] mb-1">
              Compliance Issues:
            </div>
            <ul className="text-sm text-muted-foreground space-y-1">
              {!compliance.trailing_threshold.passed && (
                <li>" Trailing drawdown exceeded limit</li>
              )}
              {!compliance.max_contracts.passed && (
                <li>" Maximum contract limit exceeded</li>
              )}
              {!compliance.trading_hours.compliant && (
                <li>" Trading outside allowed hours detected</li>
              )}
              {!compliance.profit_goal.passed && (
                <li>" Profit goal not met</li>
              )}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}