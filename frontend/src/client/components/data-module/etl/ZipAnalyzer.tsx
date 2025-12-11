import React, { useState } from 'react';
import { X, AlertTriangle, FileText, Calendar, Database, Clock, Upload, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { apiClient } from '@/services/api';

interface ZipAnalysisResult {
  zip_filename: string;
  zip_size_mb: number;
  total_files: number;
  total_csv_files: number;
  csv_files: Array<{
    filename: string;
    symbol: string;
    date: string | null;
    size_mb: number;
    estimated_ticks: number;
    already_in_db: boolean;
    compressed: boolean;
  }>;
  date_range: {
    start: string | null;
    end: string | null;
  };
  symbols: string[];
  total_estimated_ticks: number;
  duplicates_detected: number;
  days_already_in_db: Array<{
    symbol: string;
    date: string;
  }>;
  total_days: number;
  time_estimates?: {
    estimated_minutes: number;
    tick_processing_time: number;
    file_overhead_time: number;
    candle_generation_time: number;
  };
  error: string | null;
}

interface ZipAnalyzerProps {
  file: File;
  onConfirm: (file: File, overwriteExisting: boolean) => void;
  onCancel: () => void;
}

export default function ZipAnalyzer({ file, onConfirm, onCancel }: ZipAnalyzerProps) {
  const [analysis, setAnalysis] = useState<ZipAnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overwriteExisting, setOverwriteExisting] = useState(false);

  // Analyze the file on mount
  React.useEffect(() => {
    analyzeZipFile();
  }, [file]);

  const analyzeZipFile = async () => {
    setAnalyzing(true);
    setError(null);

    try {
      const analysis = await apiClient.analyzeZip(file);
      setAnalysis(analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze ZIP file');
    } finally {
      setAnalyzing(false);
    }
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatTime = (minutes: number) => {
    if (minutes < 1) return '<1 min';
    if (minutes < 60) return `~${Math.round(minutes)} min`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `~${hours}h ${mins}m`;
  };

  if (analyzing) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <Card className="w-[500px]">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              <p className="text-muted-foreground">Analyzing ZIP file...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <Card className="w-[500px]">
          <CardHeader>
            <CardTitle className="text-red-600">Analysis Error</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <div className="mt-4 flex justify-end space-x-2">
              <Button variant="outline" onClick={onCancel}>Cancel</Button>
              <Button onClick={analyzeZipFile}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!analysis) return null;

  const hasDuplicates = analysis.duplicates_detected > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto py-8">
      <Card className="w-[800px] max-h-[90vh] overflow-y-auto">
        <CardHeader className="sticky top-0 bg-background z-10 border-b">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-xl">📦 ZIP File Analysis</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">{analysis.zip_filename} ({analysis.zip_size_mb.toFixed(2)} MB)</p>
            </div>
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pt-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">CSV Files</p>
              <p className="text-2xl font-semibold">{analysis.total_csv_files}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Days of Data</p>
              <p className="text-2xl font-semibold">{analysis.total_days}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Estimated Ticks</p>
              <p className="text-2xl font-semibold">{formatNumber(analysis.total_estimated_ticks)}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Estimated Time</p>
              <p className="text-2xl font-semibold">
                {analysis.time_estimates ? formatTime(analysis.time_estimates.estimated_minutes) : 'N/A'}
              </p>
            </div>
          </div>

          {/* Date Range */}
          {analysis.date_range.start && (
            <div className="flex items-center space-x-2 p-3 bg-muted/50 rounded-md">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">
                Date range: <strong>{analysis.date_range.start}</strong> to <strong>{analysis.date_range.end}</strong>
              </span>
            </div>
          )}

          {/* Symbols */}
          {analysis.symbols.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">Detected symbols:</p>
              <div className="flex flex-wrap gap-2">
                {analysis.symbols.map(symbol => (
                  <Badge key={symbol} variant="secondary">{symbol}</Badge>
                ))}
              </div>
            </div>
          )}

          {/* Duplicates Warning */}
          {hasDuplicates && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>{analysis.duplicates_detected} days already exist</strong> in the database:
                <ul className="mt-2 text-sm space-y-1">
                  {analysis.days_already_in_db.slice(0, 5).map((day, idx) => (
                    <li key={idx}>• {day.symbol} - {day.date}</li>
                  ))}
                  {analysis.days_already_in_db.length > 5 && (
                    <li>... and {analysis.days_already_in_db.length - 5} more</li>
                  )}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* File List (collapsible) */}
          <details className="space-y-2">
            <summary className="cursor-pointer text-sm font-medium hover:text-primary">
              View file details ({analysis.csv_files.length})
            </summary>
            <div className="mt-2 max-h-60 overflow-y-auto border rounded-md">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr>
                    <th className="text-left p-2">File</th>
                    <th className="text-left p-2">Date</th>
                    <th className="text-right p-2">Est. Ticks</th>
                    <th className="text-center p-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.csv_files.map((file, idx) => (
                    <tr key={idx} className="border-t hover:bg-muted/30">
                      <td className="p-2">
                        <span className="font-mono text-xs">{file.filename}</span>
                      </td>
                      <td className="p-2">{file.date || 'N/A'}</td>
                      <td className="p-2 text-right">{formatNumber(file.estimated_ticks)}</td>
                      <td className="p-2 text-center">
                        {file.already_in_db ? (
                          <Badge variant="warning" className="text-xs">Duplicate</Badge>
                        ) : (
                          <Badge variant="success" className="text-xs">New</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>

          {/* Processing Time Breakdown */}
          {analysis.time_estimates && (
            <div className="space-y-2 p-3 bg-muted/30 rounded-md">
              <p className="text-sm font-medium">Estimated processing time:</p>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>• Tick processing:</span>
                  <span>{formatTime(analysis.time_estimates.tick_processing_time)}</span>
                </div>
                <div className="flex justify-between">
                  <span>• File operations:</span>
                  <span>{formatTime(analysis.time_estimates.file_overhead_time)}</span>
                </div>
                <div className="flex justify-between">
                  <span>• Candle generation:</span>
                  <span>{formatTime(analysis.time_estimates.candle_generation_time)}</span>
                </div>
                <div className="flex justify-between font-medium text-foreground border-t pt-1">
                  <span>Estimated total:</span>
                  <span>{formatTime(analysis.time_estimates.estimated_minutes)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Options */}
          {hasDuplicates && (
            <div className="flex items-center space-x-2 p-3 bg-yellow-500/10 rounded-md">
              <Checkbox
                id="overwrite"
                checked={overwriteExisting}
                onCheckedChange={(checked) => setOverwriteExisting(checked as boolean)}
              />
              <label
                htmlFor="overwrite"
                className="text-sm font-medium cursor-pointer"
              >
                Overwrite existing data (duplicates will be automatically ignored)
              </label>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button
              onClick={() => onConfirm(file, overwriteExisting)}
              className="gap-2"
            >
              <Upload className="h-4 w-4" />
              Process {hasDuplicates && !overwriteExisting ? 'New Files Only' : 'All'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}