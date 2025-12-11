import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileUploader } from "./FileUploader";
import { JobMonitor } from "./JobMonitor";
import { DatabaseStats } from "./DatabaseStats";
import { SymbolExplorer } from "./SymbolExplorer";
import { CoverageHeatMap } from "./CoverageHeatMap";
import { JobSummaryCards } from "./JobSummaryCards";
import { IntegrityCheck } from "./IntegrityCheck";
import type { ETLJob } from "@/types/etl";

type ETLTab = 'upload' | 'jobs' | 'symbols' | 'coverage' | 'integrity' | 'stats';

export const ETLDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ETLTab>('upload');
  const [highlightJobId, setHighlightJobId] = useState<string | null>(null);

  const handleUploadSuccess = (job: ETLJob) => {
    // Switch to Jobs tab and highlight the new job
    setHighlightJobId(job.id);
    setActiveTab('jobs');

    // Clear highlight after 5 seconds
    setTimeout(() => {
      setHighlightJobId(null);
    }, 5000);
  };

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error);
  };

  return (
    <div className="space-y-4" data-testid="etl-dashboard">
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as ETLTab)}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="upload" data-testid="upload-tab">
            Upload
          </TabsTrigger>
          <TabsTrigger value="jobs" data-testid="jobs-tab">
            Jobs
          </TabsTrigger>
          <TabsTrigger value="symbols" data-testid="symbols-tab">
            Symbols
          </TabsTrigger>
          <TabsTrigger value="coverage" data-testid="coverage-tab">
            Coverage
          </TabsTrigger>
          <TabsTrigger value="integrity" data-testid="integrity-tab">
            Integrity
          </TabsTrigger>
          <TabsTrigger value="stats" data-testid="stats-tab">
            Statistics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Upload Databento ZIP File</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Upload a ZIP file containing Databento market data. Select the timeframes
              you want to process.
            </p>
          </div>

          <FileUploader
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </TabsContent>

        <TabsContent value="jobs" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Processing Jobs</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Monitor the status of your ETL jobs. Jobs are automatically refreshed every 2 seconds while processing.
            </p>
          </div>

          <JobSummaryCards />

          <JobMonitor
            highlightJobId={highlightJobId}
            autoRefresh={true}
            refreshInterval={2000}
          />
        </TabsContent>

        <TabsContent value="symbols" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Symbol Explorer</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Explore all symbols in the database with detailed statistics including tick counts, candle data, and date ranges.
            </p>
          </div>

          <SymbolExplorer />
        </TabsContent>

        <TabsContent value="coverage" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Coverage Heat Map</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Visualize data completeness across dates and timeframes. Green indicates complete data, yellow partial, and red missing.
            </p>
          </div>

          <CoverageHeatMap />
        </TabsContent>

        <TabsContent value="integrity" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Data Integrity Check</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Verify data consistency by comparing candle counts across timeframes. Check that mathematical relationships are correct (e.g., 2 candles of 30s = 1 candle of 1min).
            </p>
          </div>

          <IntegrityCheck />
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Database Statistics</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Overview of all data stored in the database including ticks, candles, and active contract periods.
            </p>
          </div>

          <DatabaseStats />
        </TabsContent>
      </Tabs>
    </div>
  );
};
