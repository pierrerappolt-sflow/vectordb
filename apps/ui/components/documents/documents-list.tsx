"use client";

import { useState, useEffect } from "react";
import type { Document } from "@/lib/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface DocumentsListProps {
  initialDocuments: Document[];
}

export function DocumentsList({ initialDocuments }: DocumentsListProps) {
  const [documents, setDocuments] = useState<Document[]>(initialDocuments);

  // Sync with server data when it changes
  useEffect(() => {
    setDocuments(initialDocuments);
  }, [initialDocuments]);

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

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  if (documents.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <p>No documents yet. Upload one to get started.</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Fragments</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Updated</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((document) => (
          <TableRow key={document.id}>
            <TableCell className="font-medium">{document.name}</TableCell>
            <TableCell>
              <span className="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium bg-primary/10 text-primary">
                {document.status}
              </span>
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {formatBytes(document.total_bytes)}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {document.fragment_count}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {formatRelativeDate(document.created_at)}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {formatRelativeDate(document.updated_at)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
