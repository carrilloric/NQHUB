/**
 * Audit Validation Panel
 *
 * Panel for generating audit reports to validate Order Blocks against ATAS.
 * Fase 1: Order Blocks only (extensible for FVGs, Session Levels later).
 */

import { useState } from 'react';
import { Calendar, Download, FileText, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuditReport } from '@/hooks/useAuditReport';

const TIMEFRAMES = ['30s', '1min', '5min', '15min', '30min', '1hr', '4hr', 'daily', 'weekly'];

export function AuditValidationPanel() {
  const { auditReport, loading, error, generateOrderBlocksAudit, clearReport } = useAuditReport();

  // Form state
  const [symbol, setSymbol] = useState('NQZ5');
  const [timeframe, setTimeframe] = useState('5min');
  const [snapshotDate, setSnapshotDate] = useState('2025-11-06');
  const [snapshotTime, setSnapshotTime] = useState('10:00');

  const handleGenerate = async () => {
    // Combine date and time into ISO 8601 datetime string
    const snapshot_time = `${snapshotDate}T${snapshotTime}:00`;

    await generateOrderBlocksAudit({
      symbol,
      timeframe,
      snapshot_time,
    });
  };

  const handleExportMarkdown = () => {
    if (!auditReport) return;

    const blob = new Blob([auditReport.report_markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_ob_${symbol}_${timeframe}_${snapshotDate}_${snapshotTime}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Generation Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Generar Audit Report - Order Blocks
          </CardTitle>
          <CardDescription>
            Genera un reporte markdown con instrucciones para validar Order Blocks en ATAS.
            <br />
            <span className="text-xs text-muted-foreground">
              Fase 1: Solo Order Blocks (extensible para FVGs, Session Levels después)
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Symbol */}
            <div className="space-y-2">
              <Label htmlFor="symbol">Symbol</Label>
              <Input
                id="symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="NQZ5"
              />
            </div>

            {/* Timeframe */}
            <div className="space-y-2">
              <Label htmlFor="timeframe">Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger id="timeframe">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map((tf) => (
                    <SelectItem key={tf} value={tf}>
                      {tf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Snapshot Date */}
            <div className="space-y-2">
              <Label htmlFor="snapshot-date" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Snapshot Date
              </Label>
              <Input
                id="snapshot-date"
                type="date"
                value={snapshotDate}
                onChange={(e) => setSnapshotDate(e.target.value)}
              />
            </div>

            {/* Snapshot Time (UTC) */}
            <div className="space-y-2">
              <Label htmlFor="snapshot-time">
                Snapshot Time (UTC)
              </Label>
              <Input
                id="snapshot-time"
                type="time"
                value={snapshotTime}
                onChange={(e) => setSnapshotTime(e.target.value)}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              onClick={handleGenerate}
              disabled={loading}
              className="flex-1 md:flex-none"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generando...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Generar Audit Report
                </>
              )}
            </Button>

            {auditReport && (
              <>
                <Button
                  variant="outline"
                  onClick={handleExportMarkdown}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Exportar Markdown
                </Button>
                <Button
                  variant="ghost"
                  onClick={clearReport}
                >
                  Limpiar
                </Button>
              </>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive rounded-md">
              <p className="text-sm text-destructive font-medium">Error generando audit report:</p>
              <p className="text-sm text-destructive/80 mt-1">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Audit Report Display */}
      {auditReport && (
        <Card>
          <CardHeader>
            <CardTitle>Audit Report</CardTitle>
            <CardDescription>
              {auditReport.total_obs} Order Blocks activos encontrados en {auditReport.snapshot_time_est}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{auditReport.report_markdown}</ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
