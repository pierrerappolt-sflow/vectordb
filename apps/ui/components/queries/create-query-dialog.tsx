"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createQuery } from "@/lib/api-client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Search } from "lucide-react";

interface CreateQueryDialogProps {
  libraryId: string;
}

export function CreateQueryDialog({ libraryId }: CreateQueryDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [queryText, setQueryText] = useState("");
  const [topK, setTopK] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (!queryText.trim()) {
      setError("Query text cannot be empty");
      return;
    }

    setIsLoading(true);

    try {
      // TODO: Allow user to select vectorization config ID
      const configId = "default"; // Placeholder - use first available config
      await createQuery(libraryId, queryText, configId, topK);
      setQueryText("");
      setTopK(10);
      setOpen(false);

      // Immediate refresh to show the new query
      router.refresh();

      // Poll for updates every 5 seconds for the next 5 minutes
      // This catches the query completing
      let pollCount = 0;
      const maxPolls = 60; // 5 minutes total
      const pollInterval = setInterval(() => {
        pollCount++;
        router.refresh();

        if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
        }
      }, 5000);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create query");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Search className="mr-2 h-4 w-4" />
          New Query
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Semantic Search Query</DialogTitle>
          <DialogDescription>
            Search for similar content in this library using semantic similarity.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Query Text</Label>
            <Input
              id="query"
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              disabled={isLoading}
              placeholder="Enter your search query..."
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="topK">Number of Results (top_k)</Label>
            <Input
              id="topK"
              type="number"
              min={1}
              max={100}
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Number of most similar results to return (1-100)
            </p>
          </div>

          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !queryText.trim()}>
              {isLoading ? "Searching..." : "Search"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
