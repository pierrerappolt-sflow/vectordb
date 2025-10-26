import { getDocuments } from "@/lib/api-client";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DocumentsList } from "@/components/documents/documents-list";
import { UploadDocumentDialog } from "@/components/documents/upload-document-dialog";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

interface LibraryPageProps {
  params: Promise<{
    libraryId: string;
  }>;
}

export default async function LibraryPage({ params }: LibraryPageProps) {
  const { libraryId } = await params;
  let documents;
  let error;

  try {
    documents = await getDocuments(libraryId);
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to fetch documents";
  }

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-center gap-4">
          <Link href="/libraries">
            <Button variant="ghost" size="sm" className="gap-2">
              <ChevronLeft className="h-4 w-4" />
              Back to Libraries
            </Button>
          </Link>
        </div>

        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-4xl font-bold">Library Documents</h1>
          <UploadDocumentDialog libraryId={libraryId} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
            <CardDescription>
              View and manage documents in this library
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error ? (
              <div className="rounded-md bg-destructive/10 p-4 text-destructive">
                <p className="font-semibold">Error loading documents</p>
                <p className="text-sm">{error}</p>
              </div>
            ) : (
              <DocumentsList initialDocuments={documents || []} />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
