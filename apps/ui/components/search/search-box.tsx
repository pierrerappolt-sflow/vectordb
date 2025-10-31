"use client";

import { useState } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { createQuery } from "@/lib/api-client";
import { useQueryPolling } from "@/hooks/useQueryPolling";
import { DocumentScanningLoader } from "./document-scanning-loader";
import type { Query } from "@/lib/api-client";

interface SearchBoxProps {
  libraryId: string;
  onResults?: (query: Query) => void;
}

export function SearchBox({ libraryId, onResults }: SearchBoxProps) {
  const [searchText, setSearchText] = useState("");
  const [activeQueryId, setActiveQueryId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { query, isPolling, error } = useQueryPolling(libraryId, activeQueryId, {
    onComplete: (completedQuery) => {
      onResults?.(completedQuery);
      setIsSubmitting(false);
    },
    onError: () => {
      setIsSubmitting(false);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!searchText.trim() || isSubmitting) return;

    setIsSubmitting(true);

    try {
      const result = await createQuery(libraryId, searchText, 10);
      setActiveQueryId(result.query_id);
    } catch (err) {
      console.error("Failed to create query:", err);
      setIsSubmitting(false);
    }
  };

  const handleClear = () => {
    setSearchText("");
    setActiveQueryId(null);
    onResults?.(null as any); // Clear results
  };

  const isLoading = isSubmitting || isPolling;

  return (
    <Card className="p-6 space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search documents semantically..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            disabled={isLoading}
            className="pl-10 pr-10 h-12 text-base"
          />
          {searchText && (
            <button
              type="button"
              onClick={() => setSearchText("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
        <Button
          type="submit"
          disabled={!searchText.trim() || isLoading}
          size="lg"
          className="px-8"
        >
          {isLoading ? "Searching..." : "Search"}
        </Button>
        {activeQueryId && (
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={handleClear}
          >
            Clear
          </Button>
        )}
      </form>

      {isLoading && (
        <DocumentScanningLoader
          message={
            query?.status === "PROCESSING"
              ? "Analyzing documents..."
              : "Preparing search..."
          }
        />
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 p-4 text-destructive">
          <p className="font-semibold">Search Failed</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {query?.status === "COMPLETED" && query.total_results === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <p>No results found for "{query.query_text}"</p>
          <p className="text-sm mt-2">Try different search terms</p>
        </div>
      )}
    </Card>
  );
}
