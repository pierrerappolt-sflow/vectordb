"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MoreHorizontal, Trash2 } from "lucide-react";
import type { Library } from "@/lib/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { DeleteLibraryDialog } from "./delete-library-dialog";

interface LibrariesListProps {
  initialLibraries: Library[];
  onLibraryCreated?: (library: Library) => void;
}

export function LibrariesList({ initialLibraries }: LibrariesListProps) {
  const router = useRouter();
  const [libraries, setLibraries] = useState<Library[]>(initialLibraries);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedLibrary, setSelectedLibrary] = useState<Library | null>(null);

  // Sync with server data when it changes
  useEffect(() => {
    setLibraries(initialLibraries);
  }, [initialLibraries]);

  const formatRelativeDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
    return `${Math.floor(diffDays / 365)}y ago`;
  };

  const handleRowClick = (libraryId: string) => {
    router.push(`/libraries/${libraryId}`);
  };

  const handleDeleteClick = (library: Library, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click
    setSelectedLibrary(library);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (selectedLibrary) {
      // Optimistically remove from local state
      setLibraries((prev) => prev.filter((lib) => lib.id !== selectedLibrary.id));
    }
  };

  if (libraries.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <p>No libraries yet. Create one to get started.</p>
      </div>
    );
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Updated</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {libraries.map((library) => (
            <TableRow
              key={library.id}
              className="group cursor-pointer"
              onClick={() => handleRowClick(library.id)}
            >
              <TableCell className="font-medium">{library.name}</TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {formatRelativeDate(library.created_at)}
              </TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {formatRelativeDate(library.updated_at)}
              </TableCell>
              <TableCell onClick={(e) => e.stopPropagation()}>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={(e) => handleDeleteClick(library, e)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selectedLibrary && (
        <DeleteLibraryDialog
          libraryId={selectedLibrary.id}
          libraryName={selectedLibrary.name}
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          onDelete={handleDeleteConfirm}
        />
      )}
    </>
  );
}
