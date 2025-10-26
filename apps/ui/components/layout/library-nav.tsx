"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Folder } from "lucide-react";
import { getLibraries, type Library } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export function LibraryNav() {
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    async function fetchLibraries() {
      try {
        const data = await getLibraries();
        setLibraries(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load libraries");
      } finally {
        setLoading(false);
      }
    }

    fetchLibraries();
  }, []);

  // Extract current library ID from pathname
  const currentLibraryId = pathname.match(/\/libraries\/([^\/]+)/)?.[1];
  const currentLibrary = libraries.find((lib) => lib.id === currentLibraryId);

  if (loading) {
    return <div className="text-xs text-muted-foreground">Loading...</div>;
  }

  if (error) {
    return <div className="text-xs text-destructive">{error}</div>;
  }

  return (
    <div className="space-y-3">
      {/* Breadcrumb if viewing a specific library */}
      {currentLibrary && (
        <div className="mb-4 rounded-md bg-muted/50 p-2">
          <div className="flex items-center gap-1 text-xs">
            <Link
              href="/libraries"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              All Libraries
            </Link>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="text-foreground font-medium truncate">
              {currentLibrary.name}
            </span>
          </div>
        </div>
      )}

      {/* Libraries List */}
      <div className="space-y-0.5">
        {libraries.length === 0 ? (
          <div className="rounded-md border border-dashed p-4 text-center">
            <Folder className="mx-auto mb-2 h-6 w-6 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              No libraries yet
            </p>
          </div>
        ) : (
          libraries.map((library) => {
            const isActive = library.id === currentLibraryId;

            return (
              <Link
                key={library.id}
                href={`/libraries/${library.id}`}
                className={cn(
                  "group flex items-center gap-2 rounded-md px-2 py-2 text-sm transition-all",
                  isActive
                    ? "bg-accent text-accent-foreground font-medium shadow-sm"
                    : "text-foreground hover:bg-accent/50"
                )}
              >
                <Folder
                  className={cn(
                    "h-4 w-4 flex-shrink-0 transition-colors",
                    isActive
                      ? "text-accent-foreground"
                      : "text-muted-foreground group-hover:text-accent-foreground"
                  )}
                />
                <span className="truncate">{library.name}</span>
              </Link>
            );
          })
        )}
      </div>

      {/* View All Link */}
      {!pathname.startsWith("/libraries") && libraries.length > 0 && (
        <Link
          href="/libraries"
          className="mt-3 flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <span>View all libraries</span>
          <ChevronRight className="h-3 w-3" />
        </Link>
      )}
    </div>
  );
}
