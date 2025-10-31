"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Upload, CheckCircle2, Loader2, FileText } from "lucide-react";
import { uploadDocument } from "@/lib/api-client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SampleDocument {
  filename: string;
  content: string;
}

interface UploadStatus {
  filename: string;
  status: "pending" | "uploading" | "completed" | "failed";
  progress: number;
  error?: string;
}

export default function SampleUploadPage() {
  const params = useParams();
  const router = useRouter();
  const libraryId = params.libraryId as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sampleDocuments, setSampleDocuments] = useState<SampleDocument[]>([]);
  const [uploadStatuses, setUploadStatuses] = useState<UploadStatus[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  // Fetch sample documents on mount
  useEffect(() => {
    async function fetchSampleDocuments() {
      try {
        setLoading(true);
        const response = await fetch("/api/sample-documents?count=100");

        if (!response.ok) {
          throw new Error("Failed to fetch sample documents");
        }

        const data = await response.json();
        setSampleDocuments(data.documents);

        // Initialize upload statuses
        setUploadStatuses(
          data.documents.map((doc: SampleDocument) => ({
            filename: doc.filename,
            status: "pending" as const,
            progress: 0,
          }))
        );

        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load sample documents");
      } finally {
        setLoading(false);
      }
    }

    fetchSampleDocuments();
  }, []);

  // Start upload process when documents are loaded
  useEffect(() => {
    // Check if we're done
    if (sampleDocuments.length > 0 && currentIndex >= sampleDocuments.length) {
      setIsComplete(true);
      return;
    }

    // Check if we should upload next document
    if (sampleDocuments.length === 0 || currentIndex >= sampleDocuments.length) {
      return;
    }

    // Upload the current document
    async function uploadCurrentDocument() {
      const doc = sampleDocuments[currentIndex];

      // Update status to uploading
      setUploadStatuses((prev) =>
        prev.map((status, index) =>
          index === currentIndex ? { ...status, status: "uploading" as const } : status
        )
      );

      try {
        // Create File object from document content
        const blob = new Blob([doc.content], { type: "text/plain" });
        const file = new File([blob], doc.filename, { type: "text/plain" });

        // Upload with progress tracking
        await uploadDocument(libraryId, file, (percent) => {
          setUploadStatuses((prev) =>
            prev.map((status, index) =>
              index === currentIndex ? { ...status, progress: percent } : status
            )
          );
        });

        // Mark as completed
        setUploadStatuses((prev) =>
          prev.map((status, index) =>
            index === currentIndex
              ? { ...status, status: "completed" as const, progress: 100 }
              : status
          )
        );

        // Move to next document
        setCurrentIndex((prev) => prev + 1);
      } catch (e) {
        // Mark as failed
        setUploadStatuses((prev) =>
          prev.map((status, index) =>
            index === currentIndex
              ? {
                  ...status,
                  status: "failed" as const,
                  error: e instanceof Error ? e.message : "Upload failed",
                }
              : status
          )
        );

        // Continue to next document even if one fails
        setCurrentIndex((prev) => prev + 1);
      }
    }

    uploadCurrentDocument();
  }, [sampleDocuments, currentIndex, libraryId]);

  function handleViewLibrary() {
    router.push(`/libraries/${libraryId}`);
  }

  if (loading) {
    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-4xl">
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="mb-4 h-12 w-12 animate-spin text-muted-foreground" />
              <CardTitle className="mb-2">Loading sample documents...</CardTitle>
              <CardDescription>Fetching hundreds of documents from Wikipedia. This can take a minute...</CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-4xl">
          <div className="rounded-md border border-destructive bg-destructive/10 p-4">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const completedCount = uploadStatuses.filter((s) => s.status === "completed").length;
  const failedCount = uploadStatuses.filter((s) => s.status === "failed").length;
  const totalCount = uploadStatuses.length;
  const overallProgress = (completedCount / totalCount) * 100;

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h1 className="text-4xl font-bold">Uploading Sample Documents</h1>
          <p className="mt-2 text-muted-foreground">
            Creating library with 100 Wikipedia articles
          </p>
        </div>

        {/* Overall Progress */}
        <Card>
          <CardHeader>
            <CardTitle>Overall Progress</CardTitle>
            <CardDescription>
              {completedCount} of {totalCount} documents uploaded
              {failedCount > 0 && ` (${failedCount} failed)`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={overallProgress} />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{Math.round(overallProgress)}% complete</span>
              <span>
                {completedCount}/{totalCount}
              </span>
            </div>
            {isComplete && (
              <div className="flex items-center justify-center gap-2 pt-4">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                <span className="font-medium text-green-500">All documents uploaded!</span>
                <Button onClick={handleViewLibrary} className="ml-4">
                  View Library
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Current Upload */}
        {!isComplete && currentIndex < uploadStatuses.length && (
          <Card>
            <CardHeader>
              <CardTitle>Currently Uploading</CardTitle>
              <CardDescription>{uploadStatuses[currentIndex].filename}</CardDescription>
            </CardHeader>
            <CardContent>
              <Progress value={uploadStatuses[currentIndex].progress} />
              <p className="mt-2 text-sm text-muted-foreground">
                {uploadStatuses[currentIndex].progress}%
              </p>
            </CardContent>
          </Card>
        )}

        {/* Upload Queue */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Queue</CardTitle>
            <CardDescription>Status of all documents</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {uploadStatuses.map((status, index) => (
                  <div
                    key={`${status.filename}-${index}`}
                    className="flex items-center gap-3 rounded-md border p-3"
                  >
                    <div className="flex-shrink-0">
                      {status.status === "completed" && (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      )}
                      {status.status === "uploading" && (
                        <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                      )}
                      {status.status === "failed" && (
                        <FileText className="h-5 w-5 text-red-500" />
                      )}
                      {status.status === "pending" && (
                        <FileText className="h-5 w-5 text-muted-foreground" />
                      )}
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <p className="truncate text-sm font-medium">{status.filename}</p>
                      {status.error && (
                        <p className="truncate text-xs text-red-500">{status.error}</p>
                      )}
                    </div>
                    <div className="flex-shrink-0 text-xs text-muted-foreground">
                      {status.status === "completed" && "✓"}
                      {status.status === "uploading" && `${status.progress}%`}
                      {status.status === "failed" && "Failed"}
                      {status.status === "pending" && "Pending"}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
