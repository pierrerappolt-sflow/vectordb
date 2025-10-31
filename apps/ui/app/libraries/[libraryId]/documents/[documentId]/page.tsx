import Link from "next/link";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { getDocument, getLibrary } from "@/lib/api-client";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type PageProps = {
  params: Promise<{ libraryId: string; documentId: string }>;
};

export default async function DocumentDetailPage({ params }: PageProps) {
  const { libraryId, documentId } = await params;

  try {
    const [doc, library] = await Promise.all([
      getDocument(libraryId, documentId),
      getLibrary(libraryId),
    ]);

    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-6xl space-y-8">
          <PageHeader
            breadcrumbs={[
              { label: "Libraries", href: "/libraries" },
              { label: library.name, href: `/libraries/${libraryId}` },
              { label: doc.name },
            ]}
            title={doc.name}
            description={`${doc.fragment_count} fragments • ${(doc.total_bytes / 1024).toFixed(2)} KB • Status: ${doc.status}`}
          />

          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Content</h2>
          </div>

          <Suspense fallback={<div className="text-muted-foreground">Loading content…</div>}>
            {/* FragmentsList removed - fragments not in Document API response */}
            <div className="text-muted-foreground">Document content view coming soon</div>
          </Suspense>
        </div>
      </div>
    );
  } catch (error) {
    console.error("Error loading document:", error);
    notFound();
  }
}

function FragmentsList({
  fragments,
}: {
  fragments: Array<{
    id: string;
    document_id: string;
    sequence_number: number;
    size_bytes: number;
    content: string;
    content_hash: string;
    is_final: boolean;
    created_at: string;
    updated_at: string;
  }>;
}) {
  if (!fragments || fragments.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <p>No fragments available yet.</p>
          <p className="mt-2 text-sm">The document upload may still be in progress.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="prose max-w-none py-6">
        <div className="whitespace-pre-wrap leading-relaxed">
          {fragments.map((fragment) => (
            <span key={fragment.id}>{fragment.content}</span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}


