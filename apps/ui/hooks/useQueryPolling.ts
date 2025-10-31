import { useState, useEffect, useCallback, useRef } from "react";
import type { Query } from "@/lib/api-client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.pierrestack.com";

interface UseQueryPollingOptions {
  interval?: number;
  onComplete?: (query: Query) => void;
  onError?: (error: string) => void;
}

interface UseQueryPollingResult {
  query: Query | null;
  isPolling: boolean;
  error: string | null;
  stopPolling: () => void;
}

export function useQueryPolling(
  libraryId: string | null,
  queryId: string | null,
  options: UseQueryPollingOptions = {}
): UseQueryPollingResult {
  const { interval = 2000, onComplete, onError } = options;

  const [query, setQuery] = useState<Query | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const hasCompletedRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const fetchQuery = useCallback(async () => {
    if (!libraryId || !queryId) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/libraries/${libraryId}/queries/${queryId}`,
        { cache: "no-store" }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch query: ${response.statusText}`);
      }

      const data: Query = await response.json();
      setQuery(data);

      // Check if query is in terminal state
      if (data.status === "COMPLETED") {
        if (!hasCompletedRef.current) {
          hasCompletedRef.current = true;
          onComplete?.(data);
        }
        stopPolling();
      } else if (data.status === "FAILED") {
        const errorMsg = "error_message" in data ? (data as any).error_message : "Query failed";
        setError(errorMsg);
        onError?.(errorMsg);
        stopPolling();
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      setError(errorMsg);
      onError?.(errorMsg);
      stopPolling();
    }
  }, [libraryId, queryId, onComplete, onError, stopPolling]);

  useEffect(() => {
    if (!libraryId || !queryId) {
      stopPolling();
      return;
    }

    // Reset state when queryId changes
    hasCompletedRef.current = false;
    setError(null);
    setIsPolling(true);

    // Immediate first fetch
    fetchQuery();

    // Start polling
    intervalRef.current = setInterval(fetchQuery, interval);

    return () => {
      stopPolling();
    };
  }, [libraryId, queryId, interval, fetchQuery, stopPolling]);

  return {
    query,
    isPolling,
    error,
    stopPolling,
  };
}
