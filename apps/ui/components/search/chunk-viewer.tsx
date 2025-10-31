"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SearchResult } from "@/lib/api-client";

interface ChunkViewerProps {
  result: SearchResult;
  queryText: string;
  index: number;
}

export function ChunkViewer({ result, queryText, index }: ChunkViewerProps) {
  const [showContext, setShowContext] = useState(false);

  // Highlight matched text (simple word-based highlighting)
  const highlightText = (text: string) => {
    const words = queryText.toLowerCase().split(/\s+/);
    let highlightedText = text;

    words.forEach((word) => {
      if (word.length > 2) {
        const regex = new RegExp(`(${word})`, "gi");
        highlightedText = highlightedText.replace(
          regex,
          '<mark class="bg-yellow-200 dark:bg-yellow-900 px-1 rounded">$1</mark>'
        );
      }
    });

    return highlightedText;
  };

  return (
    <Card className="p-6 space-y-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <div className="mt-1">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="font-mono text-xs">
                Result #{index + 1}
              </Badge>
              <Badge variant="outline" className="text-xs">
                Score: {result.similarity_score.toFixed(3)}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground font-mono">
              Doc: {result.document_id.slice(0, 8)}... | Chunk: {result.chunk_id.slice(0, 8)}...
            </p>
          </div>
        </div>
      </div>

      {/* Matched chunk content */}
      <div className="space-y-3">
        <div className="border-l-4 border-primary/40 pl-4 py-2">
          <p
            className="text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: highlightText(result.text) }}
          />
        </div>

        {/* Context toggle */}
        <div className="flex justify-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowContext(!showContext)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            {showContext ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1" />
                Hide context
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1" />
                Show more context
              </>
            )}
          </Button>
        </div>

        {/* Extended context (placeholder - would load from API) */}
        {showContext && (
          <div className="space-y-3 pt-2 border-t">
            <div className="text-xs text-muted-foreground italic">
              Context before:
            </div>
            <div className="bg-muted/30 rounded-lg p-4 text-sm text-muted-foreground">
              <p>
                [Context loading would happen here - chunks before this match would be fetched from
                GET /libraries/{`{libraryId}`}/chunks/{`{chunkId}`}/context]
              </p>
            </div>

            <div className="border-l-4 border-primary/40 pl-4 py-2 bg-primary/5 rounded">
              <div className="text-xs text-primary font-semibold mb-2">Matched chunk:</div>
              <p
                className="text-sm leading-relaxed"
                dangerouslySetInnerHTML={{ __html: highlightText(result.text) }}
              />
            </div>

            <div className="text-xs text-muted-foreground italic">
              Context after:
            </div>
            <div className="bg-muted/30 rounded-lg p-4 text-sm text-muted-foreground">
              <p>
                [Context loading would happen here - chunks after this match would be fetched]
              </p>
            </div>

            <div className="flex justify-center pt-2">
              <Button variant="outline" size="sm" disabled>
                View Full Document
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
