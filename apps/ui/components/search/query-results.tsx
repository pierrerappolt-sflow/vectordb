"use client";

import { ChunkViewer } from "./chunk-viewer";
import type { Query } from "@/lib/api-client";
import { FileText } from "lucide-react";
import { Card } from "@/components/ui/card";

interface QueryResultsProps {
  query: Query;
}

export function QueryResults({ query }: QueryResultsProps) {
  if (!query.results || query.results.length === 0) {
    return null;
  }

  // Group results by document
  const resultsByDocument = query.results.reduce((acc, result) => {
    const docId = result.document_id;
    if (!acc[docId]) {
      acc[docId] = {
        title: result.document_title || `Document ${docId.slice(0, 8)}`,
        results: [],
      };
    }
    acc[docId].results.push(result);
    return acc;
  }, {} as Record<string, { title: string; results: typeof query.results }>);

  return (
    <div className="space-y-6">
      {/* Results header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Search Results</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Found {query.total_results} {query.total_results === 1 ? "match" : "matches"} across{" "}
            {Object.keys(resultsByDocument).length}{" "}
            {Object.keys(resultsByDocument).length === 1 ? "document" : "documents"}
          </p>
        </div>
        <div className="text-sm text-muted-foreground">
          Query: <span className="font-medium text-foreground">"{query.query_text}"</span>
        </div>
      </div>

      {/* Results grouped by document */}
      {Object.entries(resultsByDocument).map(([documentId, { title, results }]) => (
        <div key={documentId} className="space-y-4">
          {/* Document header */}
          <Card className="bg-muted/30 p-4">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-primary flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-base truncate" title={title}>
                  {title}
                </h3>
                <p className="text-xs text-muted-foreground font-mono truncate" title={documentId}>
                  {documentId}
                </p>
              </div>
              <div className="text-sm text-muted-foreground flex-shrink-0">
                {results.length} {results.length === 1 ? "match" : "matches"}
              </div>
            </div>
          </Card>

          {/* Chunks for this document */}
          <div className="space-y-3 pl-8">
            {results.map((result, index) => (
              <ChunkViewer
                key={result.chunk_id}
                result={result}
                queryText={query.query_text}
                index={index}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
