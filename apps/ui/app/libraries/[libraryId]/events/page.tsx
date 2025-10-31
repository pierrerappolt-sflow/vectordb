"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getEventLogs, getLibrary, GetEventLogsResponse, type Library } from "@/lib/api-client";
import { EventLogViewer } from "@/components/events/event-log-viewer";
import { PageHeader } from "@/components/ui/page-header";
import { Loader2 } from "lucide-react";

export default function EventsPage() {
  const params = useParams();
  const libraryId = params.libraryId as string;

  const [library, setLibrary] = useState<Library | null>(null);
  const [data, setData] = useState<GetEventLogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [libraryData, eventsData] = await Promise.all([
          getLibrary(libraryId),
          getEventLogs(libraryId),
        ]);

        setLibrary(libraryData);
        setData(eventsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [libraryId]);

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        breadcrumbs={[
          { label: "Libraries", href: "/libraries" },
          { label: library?.name || "...", href: `/libraries/${libraryId}` },
          { label: "Events" },
        ]}
        title="Event Log"
        description="View system events and activity history"
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
