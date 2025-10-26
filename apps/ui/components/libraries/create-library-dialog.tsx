"use client";

import { useState, useTransition } from "react";
import { createLibrary } from "@/app/libraries/actions";
import type { Library } from "@/lib/api-client";
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

interface CreateLibraryDialogProps {
  onLibraryCreated?: (library: Library) => void;
}

export function CreateLibraryDialog({ onLibraryCreated }: CreateLibraryDialogProps) {
  const [open, setOpen] = useState(false);
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
        setOpen(false);
      } else {
        setError(result.error);
      }
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create Library</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Library</DialogTitle>
          <DialogDescription>
            Create a new document library to organize your files.
          </DialogDescription>
        </DialogHeader>
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
            />
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
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !name.trim()}>
              {isPending ? "Creating..." : "Create"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
