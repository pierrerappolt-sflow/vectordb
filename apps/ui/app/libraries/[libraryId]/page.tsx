"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Upload, Search, Loader2, X, CheckCircle2, FileText, AlertCircle, Trash2 } from "lucide-react";
import { getDocuments, getLibrary, uploadDocument, createQuery, getQuery, deleteDocument, getLibraryConfigs, type Document, type Library, type Query, type VectorizationConfig } from "@/lib/api-client";
import { createUploadQueue, type UploadItem, type UploadQueue } from "@/lib/upload-queue";
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
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/ui/page-header";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function LibraryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const libraryId = params.libraryId as string;

  const [library, setLibrary] = useState<Library | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadQueue, setUploadQueue] = useState<UploadQueue<Document> | null>(null);
  const [uploadItems, setUploadItems] = useState<UploadItem<Document>[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Query | null>(null);
  const [libraryConfigs, setLibraryConfigs] = useState<VectorizationConfig[]>([]);
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [pollIntervalId, setPollIntervalId] = useState<NodeJS.Timeout | null>(null);
  const [showingResults, setShowingResults] = useState(false);

  async function fetchData() {
    try {
      setLoading(true);
      const [libraryData, documentsData, configsData] = await Promise.all([
        getLibrary(libraryId),
        getDocuments(libraryId),
        getLibraryConfigs(libraryId),
      ]);
      setLibrary(libraryData);
      setDocuments(documentsData);
      setLibraryConfigs(configsData.configs);
      // Auto-select first config if configs exist
      if (configsData.configs.length > 0 && !selectedConfigId) {
        setSelectedConfigId(configsData.configs[0].id);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchData();
  }, [libraryId]);

  // Poll for updates every 10 seconds for 10 minutes
  useEffect(() => {
    const startTime = Date.now();
    const TEN_MINUTES = 10 * 60 * 1000; // 10 minutes in milliseconds
    const POLL_INTERVAL = 10 * 1000; // 10 seconds

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;

      if (elapsed >= TEN_MINUTES) {
        clearInterval(interval);
        return;
      }

      // Only refresh documents, not the entire page
      getDocuments(libraryId).then(setDocuments).catch(console.error);
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [libraryId]);

  function handleFileSelect(files: FileList | null) {
    if (!files || files.length === 0) return;
    const fileArray = Array.from(files);
    setSelectedFiles((prev) => [...prev, ...fileArray]);
  }

  function handleRemoveFile(index: number) {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  }

  function startUpload() {
    if (selectedFiles.length === 0) return;

    const queue = createUploadQueue<Document>(selectedFiles, {
      maxConcurrent: 5,
      uploadFn: (file, onProgress) => uploadDocument(libraryId, file, onProgress),
      onItemUpdate: (item) => {
        setUploadItems((prev) => {
          const index = prev.findIndex((i) => i.id === item.id);
          if (index >= 0) {
            const newItems = [...prev];
            newItems[index] = item;
            return newItems;
          }
          return [...prev, item];
        });
      },
      onComplete: async () => {
        // Refresh documents list when all uploads complete
        await fetchData();
      },
    });

    setUploadQueue(queue);
    setUploadItems(queue.getItems());
    queue.start();
  }

  function handleOpenUploadDialog(open: boolean) {
    if (open) {
      // Reset state when opening dialog
      setSelectedFiles([]);
      setUploadQueue(null);
      setUploadItems([]);
      setIsUploadDialogOpen(true);
    } else {
      // Check if uploads are in progress before closing
      const stats = uploadQueue?.getStats();
      if (stats && !stats.isComplete && stats.uploading > 0) {
        if (!confirm("Uploads are in progress. Are you sure you want to close?")) {
          return;
        }
      }
      setIsUploadDialogOpen(false);
      setSelectedFiles([]);
      setUploadQueue(null);
      setUploadItems([]);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim() || !selectedConfigId) return;

    try {
      setSearching(true);
      setShowingResults(true);

      // Create the query
      const initialResult = await createQuery(libraryId, searchQuery, selectedConfigId, 10);
      setSearchResults(initialResult);

      // If query is still processing, poll for results
      if (initialResult.status === "PROCESSING" || initialResult.status === "PENDING") {
        const queryId = initialResult.query_id;
        let pollCount = 0;
        const maxPolls = 300; // 5 minutes total (300 * 1s)

        const pollInterval = setInterval(async () => {
          pollCount++;

          try {
            const updatedQuery = await getQuery(libraryId, queryId);
            setSearchResults(updatedQuery);

            // Stop polling if completed or failed
            if (updatedQuery.status === "COMPLETED" || updatedQuery.status === "FAILED") {
              clearInterval(pollInterval);
              setPollIntervalId(null);
              setSearching(false);
            }
          } catch (err) {
            console.error("Error polling query:", err);
          }

          // Stop polling after max attempts
          if (pollCount >= maxPolls) {
            clearInterval(pollInterval);
            setPollIntervalId(null);
            setSearching(false);
          }
        }, 1000); // Poll every 1 second

        setPollIntervalId(pollInterval);
      } else {
        setSearching(false);
      }
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to search");
      setSearching(false);
      setSearchResults(null);
      setShowingResults(false);
    }
  }

  function handleClearResults() {
    // Clear polling interval if active
    if (pollIntervalId) {
      clearInterval(pollIntervalId);
      setPollIntervalId(null);
    }
    setSearching(false);
    setSearchResults(null);
    setShowingResults(false);
  }

  async function handleDeleteDocument(id: string, name: string) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;

    // Optimistically remove from UI
    const previousDocuments = documents;
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));

    try {
      await deleteDocument(libraryId, id);
      // Success - keep the optimistic update, fetch to sync with server
      await fetchData();
    } catch (e) {
      // Revert optimistic update on error
      setDocuments(previousDocuments);
      alert(e instanceof Error ? e.message : "Failed to delete document");
    }
  }

  if (loading) {
    return null;
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-6xl">
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
          breadcrumbs={[
            { label: "Libraries", href: "/libraries" },
            { label: library?.name || "..." },
          ]}
          title="Library Documents"
          description="Manage documents in this library"
          actions={
            <Dialog open={isUploadDialogOpen} onOpenChange={handleOpenUploadDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Documents
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Upload Documents</DialogTitle>
                  <DialogDescription>
                    Drag & drop files or click to browse.
                  </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                  {/* Drag & Drop Zone */}
                  {!uploadQueue && (
                    <div
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`
                        relative cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors
                        ${isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"}
                      `}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        onChange={(e) => handleFileSelect(e.target.files)}
                        className="hidden"
                      />
                      <Upload className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                      <p className="mb-2 text-lg font-semibold">Drop files here or click to browse</p>
                      <p className="text-sm text-muted-foreground">
                        Any file type accepted • Multiple files supported
                      </p>
                    </div>
                  )}

                  {/* Selected Files (before upload) */}
                  {selectedFiles.length > 0 && !uploadQueue && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm font-semibold">
                          Selected Files ({selectedFiles.length})
                        </Label>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedFiles([])}
                        >
                          Clear All
                        </Button>
                      </div>
                      <ScrollArea className="max-h-[200px]">
                        <div className="space-y-2">
                          {selectedFiles.map((file, index) => (
                            <div
                              key={`${file.name}-${file.size}-${file.lastModified}-${index}`}
                              className="flex items-center justify-between rounded-lg border p-3"
                            >
                              <div className="flex items-center gap-3">
                                <FileText className="h-5 w-5 text-muted-foreground" />
                                <div>
                                  <p className="text-sm font-medium">{file.name}</p>
                                  <p className="text-xs text-muted-foreground">
                                    {(file.size / 1024).toFixed(2)} KB
                                  </p>
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRemoveFile(index)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}

                  {/* Upload Queue Status */}
                  {uploadQueue && uploadItems.length > 0 && (
                    <div className="space-y-4">
                      {/* Overall Progress */}
                      <div className="rounded-lg border p-4">
                        <div className="mb-2 flex items-center justify-between">
                          <Label className="text-sm font-semibold">Overall Progress</Label>
                          <span className="text-sm text-muted-foreground">
                            {uploadQueue.getStats().completed} of {uploadQueue.getStats().total} completed
                          </span>
                        </div>
                        <Progress value={uploadQueue.getStats().overallProgress} />
                        <p className="mt-2 text-xs text-muted-foreground">
                          {Math.round(uploadQueue.getStats().overallProgress)}% •
                          {uploadQueue.getStats().uploading} uploading •
                          {uploadQueue.getStats().failed > 0 && ` ${uploadQueue.getStats().failed} failed`}
                        </p>
                      </div>

                      {/* Upload Queue Items */}
                      <div className="space-y-2">
                        <Label className="text-sm font-semibold">Upload Queue</Label>
                        <ScrollArea className="max-h-[300px]">
                          <div className="space-y-2">
                            {uploadItems.map((item) => (
                              <div
                                key={item.id}
                                className="rounded-lg border p-3"
                              >
                                <div className="flex items-start justify-between">
                                  <div className="flex items-start gap-3 flex-1">
                                    <div className="flex-shrink-0 mt-0.5">
                                      {item.status === "completed" && (
                                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                                      )}
                                      {item.status === "uploading" && (
                                        <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                                      )}
                                      {item.status === "failed" && (
                                        <AlertCircle className="h-5 w-5 text-red-500" />
                                      )}
                                      {item.status === "pending" && (
                                        <FileText className="h-5 w-5 text-muted-foreground" />
                                      )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm font-medium truncate">
                                        {item.file.name}
                                      </p>
                                      <p className="text-xs text-muted-foreground">
                                        {(item.file.size / 1024).toFixed(2)} KB
                                      </p>
                                      {item.error && (
                                        <p className="mt-1 text-xs text-red-500">{item.error}</p>
                                      )}
                                      {item.status === "uploading" && (
                                        <Progress value={item.progress} className="mt-2" />
                                      )}
                                    </div>
                                  </div>
                                  <div className="flex-shrink-0 ml-4 text-xs text-muted-foreground">
                                    {item.status === "uploading" && `${item.progress}%`}
                                    {item.status === "completed" && "✓"}
                                    {item.status === "failed" && "Failed"}
                                    {item.status === "pending" && "Pending"}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </ScrollArea>
                      </div>

                      {/* Completion Message */}
                      {uploadQueue.getStats().isComplete && (
                        <div className="rounded-lg border border-green-500/20 bg-green-500/10 p-4">
                          <div className="flex items-center gap-2">
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                            <p className="font-medium text-green-500">
                              Upload complete! {uploadQueue.getStats().completed} files uploaded successfully
                              {uploadQueue.getStats().failed > 0 && `, ${uploadQueue.getStats().failed} failed`}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Dialog Actions */}
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleOpenUploadDialog(false)}
                  >
                    {uploadQueue?.getStats().isComplete ? "Close" : "Cancel"}
                  </Button>
                  {!uploadQueue && (
                    <Button
                      onClick={startUpload}
                      disabled={selectedFiles.length === 0}
                    >
                      Start Upload ({selectedFiles.length} {selectedFiles.length === 1 ? "file" : "files"})
                    </Button>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          }
        />

        {/* Search Section */}
        <div className="rounded-lg border bg-card p-4">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-4">
              <div className="w-[300px]">
                <Label className="text-sm font-medium mb-2 block">Config</Label>
                {libraryConfigs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No configs available.{" "}
                    <a href="/configs" className="text-primary hover:underline">
                      Create one
                    </a>
                  </p>
                ) : (
                  <Select value={selectedConfigId || undefined} onValueChange={setSelectedConfigId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select config" />
                    </SelectTrigger>
                    <SelectContent>
                      {libraryConfigs.map((config) => (
                        <SelectItem key={config.id} value={config.id}>
                          {config.description || `v${config.version} - ${config.vector_indexing_strategy}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
              <div className="flex-1">
                <Label className="text-sm font-medium mb-2 block">Search Query</Label>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    placeholder="Search documents using semantic similarity..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    disabled={!selectedConfigId}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={!searchQuery.trim() || !selectedConfigId || searching}>
                    <Search className="mr-2 h-4 w-4" />
                    {searching ? "Searching..." : "Search"}
                  </Button>
                  {showingResults && (
                    <Button type="button" variant="outline" onClick={handleClearResults}>
                      <X className="mr-2 h-4 w-4" />
                      Clear Results
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </form>
        </div>

        {/* Documents or Search Results Section */}
        {showingResults ? (
          <div>
            {/* Loading State */}
            {searching && (
              <div className="rounded-lg border bg-card p-12">
                <div className="flex flex-col items-center justify-center gap-4">
                  <Loader2 className="h-12 w-12 animate-spin text-primary" />
                  <div className="text-center">
                    <h3 className="text-lg font-semibold">Searching documents...</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      This may take a few moments
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Failed State */}
            {!searching && searchResults?.status === "FAILED" && (
              <div className="rounded-lg border border-destructive bg-destructive/10 p-8">
                <div className="flex flex-col items-center gap-4">
                  <AlertCircle className="h-12 w-12 text-destructive" />
                  <div className="text-center">
                    <h3 className="text-lg font-semibold text-destructive">Search Failed</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      An error occurred while processing your search query.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Results - Completed */}
            {!searching && searchResults?.status === "COMPLETED" && (
              <div className="space-y-4">
                {searchResults.results && searchResults.results.length > 0 ? (
                  <>
                    <div className="flex items-center justify-between mb-4">
                      <p className="text-sm text-muted-foreground">
                        Found {searchResults.total_results} matching {searchResults.total_results === 1 ? 'result' : 'results'}
                      </p>
                    </div>
                    <div className="space-y-3">
                      {searchResults.results.map((result, index) => (
                        <div
                          key={`${result.chunk_id}-${index}`}
                          className="rounded-lg border bg-card p-4 hover:bg-muted/50 transition-colors cursor-pointer"
                          onClick={() => router.push(`/libraries/${libraryId}/documents/${result.document_id}`)}
                        >
                          <div className="mb-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold text-muted-foreground">
                                #{index + 1}
                              </span>
                              <div className="h-4 w-px bg-border" />
                              <span className="text-xs text-muted-foreground">
                                Similarity: {(result.similarity_score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="text-xs text-muted-foreground font-mono">
                              Doc: {result.document_id.slice(0, 8)}...
                            </div>
                          </div>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.text}</p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="rounded-lg border bg-card p-12">
                    <div className="flex flex-col items-center gap-4">
                      <Search className="h-12 w-12 text-muted-foreground" />
                      <div className="text-center">
                        <h3 className="text-lg font-semibold">No results found</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          Try a different search query or upload more documents
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : documents.length === 0 ? (
          <div className="rounded-lg border bg-card p-12 text-center">
            <p className="mb-4 text-lg font-semibold">No documents yet</p>
            <p className="mb-6 text-sm text-muted-foreground">
              Upload your first documents to get started
            </p>
            <Button onClick={() => setIsUploadDialogOpen(true)}>
              <Upload className="mr-2 h-4 w-4" />
              Upload Documents
            </Button>
          </div>
        ) : (
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Ingestion Status</TableHead>
                  {selectedConfigId && <TableHead>Index Status</TableHead>}
                  <TableHead>Embeddings</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow
                    key={doc.id}
                    className="group cursor-pointer"
                    onClick={() => router.push(`/libraries/${libraryId}/documents/${doc.id}`)}
                  >
                    <TableCell className="font-medium">{doc.name}</TableCell>
                    <TableCell>
                      <Badge variant={doc.status === "completed" ? "default" : "secondary"}>
                        {doc.status}
                      </Badge>
                    </TableCell>
                    {selectedConfigId && (
                      <TableCell>
                        {(() => {
                          const configStatus = doc.vectorization_statuses?.find(
                            (s) => s.config_id === selectedConfigId
                          );
                          if (!configStatus) {
                            return <Badge variant="outline">not started</Badge>;
                          }
                          return (
                            <Badge
                              variant={
                                configStatus.status === "completed"
                                  ? "default"
                                  : configStatus.status === "failed"
                                  ? "destructive"
                                  : "secondary"
                              }
                            >
                              {configStatus.status}
                            </Badge>
                          );
                        })()}
                      </TableCell>
                    )}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span>
                          {selectedConfigId
                            ? (doc.embeddings_by_config_id?.[selectedConfigId] ?? 0).toLocaleString()
                            : doc.embeddings_count.toLocaleString()}
                        </span>
                        {doc.vectorization_statuses?.some(
                          (s) => s.status === "pending" || s.status === "processing"
                        ) && (
                          <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{(doc.total_bytes / 1024).toFixed(2)} KB</TableCell>
                    <TableCell>{formatRelativeDate(doc.created_at)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteDocument(doc.id, doc.name);
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
