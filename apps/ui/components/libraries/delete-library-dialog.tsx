"use client";

import { useState, useTransition } from "react";
import { deleteLibrary } from "@/app/libraries/actions";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteLibraryDialogProps {
  libraryId: string;
  libraryName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDelete?: () => void;
}

export function DeleteLibraryDialog({
  libraryId,
  libraryName,
  open,
  onOpenChange,
  onDelete,
}: DeleteLibraryDialogProps) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleDelete = () => {
    setError(null);

    startTransition(async () => {
      // Optimistically notify parent
      if (onDelete) {
        onDelete();
      }

      const result = await deleteLibrary(libraryId);

      if (result.success) {
        onOpenChange(false);
      } else {
        setError(result.error);
      }
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Library</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{libraryName}</strong>? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="default"
            onClick={handleDelete}
            disabled={isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isPending ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
