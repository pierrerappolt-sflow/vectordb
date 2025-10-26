"use client";

import { useOptimistic, useTransition, useState } from "react";
import { createLibrary } from "@/app/libraries/actions";
import type { Library } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface CreateLibraryFormProps {
  onLibraryCreated?: (library: Library) => void;
}

export function CreateLibraryForm({ onLibraryCreated }: CreateLibraryFormProps) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Library name is required");
      return;
    }

    startTransition(async () => {
      // Optimistically update UI before server responds
      if (onLibraryCreated) {
        // Create temporary optimistic library
        const now = new Date().toISOString();
        const optimisticLibrary: Library = {
          id: `temp-${Date.now()}`,
          name: name.trim(),
          created_at: now,
          updated_at: now,
        };
        onLibraryCreated(optimisticLibrary);
      }

      const result = await createLibrary(name.trim());

      if (result.success) {
        setName("");
        // Real library data will sync via revalidation
      } else {
        setError(result.error);
      }
    });
  };

  return (
    <div className="rounded-lg border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Create Your First Library</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="library-name">Library Name</Label>
          <Input
            id="library-name"
            type="text"
            placeholder="e.g., My Document Collection"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isPending}
            className="max-w-md"
          />
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <Button type="submit" disabled={isPending || !name.trim()}>
          {isPending ? "Creating..." : "Create Library"}
        </Button>
      </form>
    </div>
  );
}
