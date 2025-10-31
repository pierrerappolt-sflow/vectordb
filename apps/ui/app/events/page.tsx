"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/ui/page-header";
import { EventLogViewer } from "@/components/events/event-log-viewer";
import { getEventLogs, type GetEventLogsResponse } from "@/lib/api-client";
import { Loader2 } from "lucide-react";

export default function GlobalEventsPage() {
  const [data, setData] = useState<GetEventLogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);
        // Fetch all events without library filter
        const events = await getEventLogs();
        setData(events);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load events");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        breadcrumbs={[{ label: "Events" }]}
        title="Event Log"
        description="View system events across all libraries"
      />

      {/* Content */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-center text-destructive">
          {error}
        </div>
      ) : data ? (
        <EventLogViewer events={data.events} />
      ) : null}
      </div>
    </div>
  );
}


