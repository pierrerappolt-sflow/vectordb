"use client";

import { useState, useEffect } from "react";
import type { Query } from "@/lib/api-client";
import { formatRelativeDate } from "@/lib/format-date";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";

interface QueriesListProps {
  initialQueries: Query[];
  libraryId: string;
}

export function QueriesList({ initialQueries, libraryId }: QueriesListProps) {
  const [queries, setQueries] = useState<Query[]>(initialQueries);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Sync with server data when it changes
  useEffect(() => {
    setQueries(initialQueries);
  }, [initialQueries]);

  const toggleRow = (queryId: string) => {
    setExpandedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(queryId)) {
        newSet.delete(queryId);
      } else {
        newSet.add(queryId);
      }
      return newSet;
    });
  };

  if (queries.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <p>No queries yet. Create one to get started.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12"></TableHead>
            <TableHead>Query Text</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Results</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Completed</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {queries.map((query) => {
            const isExpanded = expandedRows.has(query.query_id);
            return (
              <>
                <TableRow key={query.query_id} className="cursor-pointer">
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-0 h-8 w-8"
                      onClick={() => toggleRow(query.query_id)}
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                  <TableCell className="font-medium max-w-md truncate">
                    {query.query_text}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={query.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {query.total_results} results
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {formatRelativeDate(query.created_at)}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {query.completed_at ? formatRelativeDate(query.completed_at) : "-"}
                  </TableCell>
                </TableRow>
                {isExpanded && query.results && query.results.length > 0 && (
                  <TableRow key={`${query.query_id}-expanded`}>
                    <TableCell colSpan={6} className="p-0">
                      <div className="bg-muted/50 p-4 space-y-2">
                        <h4 className="text-sm font-semibold mb-3">Search Results</h4>
                        {query.results.map((result, idx) => (
                          <div
                            key={result.chunk_id}
                            className="bg-background p-3 rounded-md border"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <span className="text-xs font-medium text-muted-foreground">
                                Result #{idx + 1}
                              </span>
                              <span className="text-xs font-mono text-muted-foreground">
                                Score: {result.similarity_score.toFixed(4)}
                              </span>
                            </div>
                            <p className="text-sm">{result.text}</p>
                            <div className="mt-2 text-xs text-muted-foreground">
                              <span>Chunk: {result.chunk_id.slice(0, 8)}...</span>
                              <span className="mx-2">•</span>
                              <span>Doc: {result.document_id.slice(0, 8)}...</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
