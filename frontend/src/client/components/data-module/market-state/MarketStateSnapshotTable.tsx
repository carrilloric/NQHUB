/**
 * Market State Snapshot Table
 *
 * Interactive table showing available snapshots with click-to-load functionality
 */
import React, { useState } from "react";
import { formatInTimeZone } from "date-fns-tz";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MarketStateListResponse } from "@/types/patterns";

type SnapshotInfo = MarketStateListResponse['snapshots'][0];

interface MarketStateSnapshotTableProps {
  data: MarketStateListResponse;
  onLoadSnapshot: (symbol: string, snapshotTime: string) => void;
  loading?: boolean;
}

export const MarketStateSnapshotTable: React.FC<MarketStateSnapshotTableProps> = ({
  data,
  onLoadSnapshot,
  loading = false
}) => {
  const [sortBy, setSortBy] = useState<'date' | 'patterns'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // Sort snapshots
  const sortedSnapshots = [...data.snapshots].sort((a, b) => {
    let comparison = 0;

    if (sortBy === 'date') {
      const dateA = new Date(a.snapshot_time).getTime();
      const dateB = new Date(b.snapshot_time).getTime();
      comparison = dateA - dateB;
    } else {
      comparison = a.total_patterns - b.total_patterns;
    }

    return sortOrder === 'asc' ? comparison : -comparison;
  });

  // Pagination
  const totalPages = Math.ceil(sortedSnapshots.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentSnapshots = sortedSnapshots.slice(startIndex, endIndex);

  const handleSort = (column: 'date' | 'patterns') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const handleLoadClick = (snapshot: SnapshotInfo) => {
    onLoadSnapshot(data.symbol, snapshot.snapshot_time);
  };

  return (
    <Card className="md:col-span-2">
      <CardHeader>
        <CardTitle>Available Snapshots</CardTitle>
        <CardDescription>
          Found {data.total} snapshots for {data.symbol}
          {data.snapshots.length > 0 && (
            <span className="ml-2 text-xs">
              ({formatInTimeZone(new Date(data.snapshots[0].snapshot_time), 'America/New_York', 'MMM d, yyyy')}
              {' - '}
              {formatInTimeZone(new Date(data.snapshots[data.snapshots.length - 1].snapshot_time), 'America/New_York', 'MMM d, yyyy')})
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('date')}
                >
                  Date (EST) {sortBy === 'date' && (sortOrder === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead>Time (EST)</TableHead>
                <TableHead>Time (UTC)</TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-muted/50 text-right"
                  onClick={() => handleSort('patterns')}
                >
                  Total Patterns {sortBy === 'patterns' && (sortOrder === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentSnapshots.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No snapshots available
                  </TableCell>
                </TableRow>
              ) : (
                currentSnapshots.map((snapshot, index) => {
                  const snapshotDate = new Date(snapshot.snapshot_time);
                  const estDate = formatInTimeZone(snapshotDate, 'America/New_York', 'MMM d, yyyy');
                  const estTime = formatInTimeZone(snapshotDate, 'America/New_York', 'HH:mm:ss');
                  const utcTime = formatInTimeZone(snapshotDate, 'UTC', 'HH:mm:ss');

                  return (
                    <TableRow
                      key={`${snapshot.snapshot_time}-${index}`}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleLoadClick(snapshot)}
                    >
                      <TableCell className="font-medium">{estDate}</TableCell>
                      <TableCell>{estTime}</TableCell>
                      <TableCell className="text-muted-foreground">{utcTime}</TableCell>
                      <TableCell className="text-right">
                        <span className={`font-semibold ${
                          snapshot.total_patterns > 50 ? 'text-green-600 dark:text-green-400' :
                          snapshot.total_patterns > 20 ? 'text-blue-600 dark:text-blue-400' :
                          'text-muted-foreground'
                        }`}>
                          {snapshot.total_patterns}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleLoadClick(snapshot);
                          }}
                          disabled={loading}
                        >
                          Load
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              Showing {startIndex + 1}-{Math.min(endIndex, data.total)} of {data.total}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <div className="flex items-center gap-2">
                <span className="text-sm">
                  Page {currentPage} of {totalPages}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
