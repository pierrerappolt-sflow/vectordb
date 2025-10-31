"use client";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronLeft, ChevronRight, Filter, X } from "lucide-react";

interface EventFiltersProps {
  eventType: string | undefined;
  aggregateType: string | undefined;
  currentPage: number;
  totalEvents: number;
  eventsPerPage: number;
  onEventTypeChange: (value: string | undefined) => void;
  onAggregateTypeChange: (value: string | undefined) => void;
  onPageChange: (page: number) => void;
}

export function EventFilters({
  eventType,
  aggregateType,
  currentPage,
  totalEvents,
  eventsPerPage,
  onEventTypeChange,
  onAggregateTypeChange,
  onPageChange,
}: EventFiltersProps) {
  const totalPages = Math.ceil(totalEvents / eventsPerPage);
  const hasFilters = eventType || aggregateType;

  const clearFilters = () => {
    onEventTypeChange(undefined);
    onAggregateTypeChange(undefined);
    onPageChange(1);
  };

  return (
    <div className="flex flex-col gap-4 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between">
      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Filter className="h-4 w-4" />
          <span>Filters</span>
        </div>

        <div className="flex gap-2">
          <Select value={eventType || "all"} onValueChange={(v) => onEventTypeChange(v === "all" ? undefined : v)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Event Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Events</SelectItem>
              <SelectItem value="LibraryCreated">Library Created</SelectItem>
              <SelectItem value="DocumentCreated">Document Created</SelectItem>
              <SelectItem value="DocumentUpdated">Document Updated</SelectItem>
              <SelectItem value="ChunkProcessed">Chunk Processed</SelectItem>
              <SelectItem value="EmbeddingGenerated">Embedding Generated</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={aggregateType || "all"}
            onValueChange={(v) => onAggregateTypeChange(v === "all" ? undefined : v)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Aggregate Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="Library">Library</SelectItem>
              <SelectItem value="Document">Document</SelectItem>
              <SelectItem value="Chunk">Chunk</SelectItem>
              <SelectItem value="Embedding">Embedding</SelectItem>
            </SelectContent>
          </Select>

          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-1">
              <X className="h-4 w-4" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          Page {currentPage} of {totalPages || 1} ({totalEvents} events)
        </span>
        <div className="flex gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages || totalEvents === 0}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
