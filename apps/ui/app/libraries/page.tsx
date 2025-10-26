import { getLibraries } from "@/lib/api-client";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LibrariesList } from "@/components/libraries/libraries-list";
import { CreateLibraryDialog } from "@/components/libraries/create-library-dialog";

export default async function LibrariesPage() {
  let libraries;
  let error;

  try {
    libraries = await getLibraries();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to fetch libraries";
  }

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-4xl font-bold">Libraries</h1>
          <CreateLibraryDialog />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Library Management</CardTitle>
            <CardDescription>
              View and manage your document libraries
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error ? (
              <div className="rounded-md bg-destructive/10 p-4 text-destructive">
                <p className="font-semibold">Error loading libraries</p>
                <p className="text-sm">{error}</p>
              </div>
            ) : (
              <LibrariesList initialLibraries={libraries || []} />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
