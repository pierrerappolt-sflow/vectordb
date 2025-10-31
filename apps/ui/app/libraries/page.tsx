"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2 } from "lucide-react";
import { getLibraries, createLibrary, deleteLibrary, type Library } from "@/lib/api-client";
import { formatRelativeDate } from "@/lib/format-date";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";

export default function LibrariesPage() {
  const router = useRouter();
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newLibraryName, setNewLibraryName] = useState("");
  const [creating, setCreating] = useState(false);

  async function fetchLibraries() {
    try {
      setLoading(true);
      const data = await getLibraries();
      setLibraries(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load libraries");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchLibraries();
  }, []);

  async function handleCreateLibrary() {
    if (!newLibraryName.trim()) return;

    try {
      setCreating(true);
      const newLibrary = await createLibrary(newLibraryName);
      setNewLibraryName("");
      setIsCreateDialogOpen(false);
      // Navigate directly to the newly created library
      router.push(`/libraries/${newLibrary.id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to create library");
    } finally {
      setCreating(false);
    }
  }

  async function handleCreateSampleLibrary() {
    try {
      setCreating(true);
      const newLibrary = await createLibrary("Wikipedia Pages");
      setIsCreateDialogOpen(false);
      // Set authorization flag for sample upload page
      sessionStorage.setItem(`sample-upload-${newLibrary.id}`, "true");
      // Navigate to sample upload page
      router.push(`/libraries/${newLibrary.id}/sample-upload`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to create sample library");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteLibrary(id: string, name: string) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;

    // Optimistically remove from UI
    const previousLibraries = libraries;
    setLibraries((prev) => prev.filter((lib) => lib.id !== id));

    try {
      await deleteLibrary(id);
      // Success - keep the optimistic update, fetch to sync with server
      await fetchLibraries();
    } catch (e) {
      // Revert optimistic update on error
      setLibraries(previousLibraries);
      alert(e instanceof Error ? e.message : "Failed to delete library");
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-8 text-4xl font-bold">My Libraries</h1>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-8 text-4xl font-bold">My Libraries</h1>
          <div className="rounded-md border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <PageHeader
          breadcrumbs={[{ label: "Libraries" }]}
          title="My Libraries"
          description="Manage your document libraries and collections"
          actions={
            <>
              <Button variant="outline" onClick={handleCreateSampleLibrary} disabled={creating}>
                Load Sample Library
              </Button>
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Library
                </Button>
              </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Library</DialogTitle>
                <DialogDescription>
                  Enter a name for your new document library.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Library Name</Label>
                  <Input
                    id="name"
                    value={newLibraryName}
                    onChange={(e) => setNewLibraryName(e.target.value)}
                    placeholder="My Documents"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !creating) {
                        handleCreateLibrary();
                      }
                    }}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                  disabled={creating}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateLibrary} disabled={creating || !newLibraryName.trim()}>
                  {creating ? "Creating..." : "Create Library"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
            </>
          }
        />

        {libraries.length === 0 ? (
          <div className="rounded-lg border bg-card p-12 text-center">
            <p className="mb-4 text-lg font-semibold">No libraries yet</p>
            <p className="mb-6 text-sm text-muted-foreground">
              Create your first library to get started
            </p>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Library
            </Button>
          </div>
        ) : (
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {libraries.map((library) => (
                  <TableRow
                    key={library.id}
                    className="group cursor-pointer"
                    onClick={() => router.push(`/libraries/${library.id}`)}
                  >
                    <TableCell className="font-medium">{library.name}</TableCell>
                    <TableCell>
                      <Badge variant={library.status === "ACTIVE" ? "default" : "secondary"}>
                        {library.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatRelativeDate(library.created_at)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteLibrary(library.id, library.name);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive transition-opacity"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
