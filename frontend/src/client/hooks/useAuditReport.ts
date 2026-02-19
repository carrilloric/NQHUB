/**
 * useAuditReport Hook
 *
 * Hook for generating audit reports to validate detected patterns against ATAS.
 */

import { useState } from 'react';
import { apiClient, ApiClient } from '@/services/api';
import type {
  AuditOrderBlocksRequest,
  AuditOrderBlocksResponse,
} from '@/types/audit';

interface UseAuditReportReturn {
  /** Audit report data */
  auditReport: AuditOrderBlocksResponse | null;
  /** Loading state */
  loading: boolean;
  /** Error message if generation failed */
  error: string | null;
  /** Generate audit report for Order Blocks */
  generateOrderBlocksAudit: (request: AuditOrderBlocksRequest) => Promise<void>;
  /** Clear audit report */
  clearReport: () => void;
}

/**
 * Hook for generating audit reports
 *
 * @example
 * ```tsx
 * const { auditReport, loading, error, generateOrderBlocksAudit } = useAuditReport();
 *
 * const handleGenerate = async () => {
 *   await generateOrderBlocksAudit({
 *     symbol: 'NQZ5',
 *     timeframe: '5min',
 *     snapshot_time: '2025-11-06T10:00:00'
 *   });
 * };
 * ```
 */
export function useAuditReport(): UseAuditReportReturn {
  const [auditReport, setAuditReport] = useState<AuditOrderBlocksResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateOrderBlocksAudit = async (request: AuditOrderBlocksRequest): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.generateOrderBlocksAudit(request);
      setAuditReport(response);
    } catch (err) {
      const errorMessage = ApiClient.getErrorMessage(err);
      setError(errorMessage);
      console.error('Failed to generate audit report:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearReport = () => {
    setAuditReport(null);
    setError(null);
  };

  return {
    auditReport,
    loading,
    error,
    generateOrderBlocksAudit,
    clearReport,
  };
}
