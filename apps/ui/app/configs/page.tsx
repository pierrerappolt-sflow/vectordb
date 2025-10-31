"use client";

import { useEffect, useState } from "react";
import { getVectorizationConfigs, type VectorizationConfig } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function VectorizationConfigsPage() {
  const [configs, setConfigs] = useState<VectorizationConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchConfigs() {
    try {
      setLoading(true);
      const data = await getVectorizationConfigs();
      setConfigs(data.configs);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load vectorization configs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchConfigs();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-8 text-4xl font-bold">Vectorization Configs</h1>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-8 text-4xl font-bold">Vectorization Configs</h1>
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
          breadcrumbs={[{ label: "Vectorization Configs" }]}
          title="Vectorization Configs"
          description="Global vectorization configurations that can be associated with libraries"
        />

        {configs.length === 0 ? (
          <div className="rounded-lg border bg-card p-12 text-center">
            <p className="mb-4 text-lg font-semibold">No vectorization configs found</p>
            <p className="text-sm text-muted-foreground">
              Vectorization configs are created and managed through the system configuration
            </p>
          </div>
        ) : (
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Chunking Strategy</TableHead>
                  <TableHead>Embedding Strategy</TableHead>
                  <TableHead>Indexing Strategy</TableHead>
                  <TableHead>Similarity Metric</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {configs.map((config) => (
                  <TableRow key={config.id} className="group">
                    <TableCell className="font-medium">v{config.version}</TableCell>
                    <TableCell>
                      <Badge variant={config.status === "ACTIVE" ? "default" : "secondary"}>
                        {config.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="max-w-md truncate">{config.description || "—"}</div>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs">
                        {config.chunking_strategy_names.length > 0
                          ? config.chunking_strategy_names.join(", ")
                          : "—"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs">
                        {config.embedding_strategy_names.length > 0
                          ? config.embedding_strategy_names.join(", ")
                          : "—"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs">{config.vector_indexing_strategy}</span>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs">{config.vector_similarity_metric}</span>
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
