"use client";

import { useState } from "react";
import { EventLog } from "@/lib/api-client";
import { formatRelativeDate } from "@/lib/format-date";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EventDetailModal } from "./event-detail-modal";

interface EventLogViewerProps {
  events: EventLog[];
}

export function EventLogViewer({ events }: EventLogViewerProps) {
  const [selectedEvent, setSelectedEvent] = useState<EventLog | null>(null);

  const shortenId = (id: string) => {
    return id.length > 12 ? `${id.substring(0, 12)}...` : id;
  };

  if (events.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <p>No events found</p>
      </div>
    );
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Event Type</TableHead>
            <TableHead>Aggregate Type</TableHead>
            <TableHead>Aggregate ID</TableHead>
            <TableHead>Timestamp</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow
              key={event.id}
              className="cursor-pointer"
              onClick={() => setSelectedEvent(event)}
            >
              <TableCell className="font-medium">{event.event_type}</TableCell>
              <TableCell>{event.aggregate_type}</TableCell>
              <TableCell className="font-mono text-xs">{shortenId(event.aggregate_id)}</TableCell>
              <TableCell>{formatRelativeDate(event.occurred_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selectedEvent && (
        <EventDetailModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
      )}
    </>
  );
}
