import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Badge } from "@/components/ui/badge";
import { Database, Inbox, Server, Upload, Search, FolderOpen, Workflow, FileText } from "lucide-react";

export default function DocsPage() {
  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <PageHeader
          breadcrumbs={[{ label: "Docs" }]}
          title="Documentation"
          description="Learn how to use the VectorDB application and access infrastructure services"
        />

        {/* Quick Start Guide */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Quick Start Guide
            </CardTitle>
            <CardDescription>Get started with VectorDB in 3 simple steps</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">1</Badge>
                <div>
                  <p className="font-medium">Create a Library</p>
                  <p className="text-sm text-muted-foreground">
                    Go to the Libraries page and create a new library to organize your documents.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">2</Badge>
                <div>
                  <p className="font-medium">Upload Documents</p>
                  <p className="text-sm text-muted-foreground">
                    Click "Upload Documents" to add files. Supports multiple files and drag & drop. Up to 5 files are uploaded concurrently.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">3</Badge>
                <div>
                  <p className="font-medium">Search Your Documents</p>
                  <p className="text-sm text-muted-foreground">
                    Use semantic search to find relevant content. The system uses embeddings to understand context and meaning.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Architecture Overview */}
        <Card>
          <CardHeader>
            <CardTitle>System Architecture</CardTitle>
            <CardDescription>How VectorDB processes and stores your documents</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-medium">Document Ingestion Pipeline</h4>
              <ol className="space-y-2 text-sm text-muted-foreground">
                <li>1. Documents are uploaded and stored in PostgreSQL</li>
                <li>2. Documents are split into fragments for chunking</li>
                <li>3. Temporal workflows orchestrate the processing pipeline</li>
                <li>4. Text is chunked using configurable strategies</li>
                <li>5. Chunks are converted to embeddings using the configured provider</li>
                <li>6. Embeddings are stored in pgvector for semantic search</li>
              </ol>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Event-Driven Architecture</h4>
              <p className="text-sm text-muted-foreground">
                The system uses event sourcing to track all changes. Every action generates domain events that are:
              </p>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Stored in the event log for audit trails</li>
                <li>• Published to RabbitMQ for async processing</li>
                <li>• Used to trigger workflows in Temporal</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Infrastructure Access */}
        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-bold">Infrastructure Access</h2>
            <p className="text-muted-foreground">
              Access credentials and URLs for all infrastructure services. Click service names in the sidebar to open their interfaces.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* PostgreSQL */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  PostgreSQL Database
                </CardTitle>
                <CardDescription>PostgreSQL 15 with pgvector extension</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Connection URL</p>
                  <code className="text-sm">postgresql://vdbuser:vdbpass@localhost:5432/vectordb</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Database</p>
                  <code className="text-sm">vectordb</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Username</p>
                  <code className="text-sm">vdbuser</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Password</p>
                  <code className="text-sm">vdbpass</code>
                </div>
                <p className="pt-2 text-xs text-muted-foreground">
                  Click "Postgres" in the sidebar to access the database admin UI.
                </p>
              </CardContent>
            </Card>

            {/* RabbitMQ */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Inbox className="h-5 w-5" />
                  RabbitMQ Message Queue
                </CardTitle>
                <CardDescription>Message broker for event-driven architecture</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Management UI</p>
                  <code className="text-sm">http://localhost:15672</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">AMQP Port</p>
                  <code className="text-sm">amqp://localhost:5672</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Username</p>
                  <code className="text-sm">guest</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Password</p>
                  <code className="text-sm">guest</code>
                </div>
                <p className="pt-2 text-xs text-muted-foreground">
                  Click "RabbitMQ" in the sidebar to access the management console.
                </p>
              </CardContent>
            </Card>

            {/* Temporal */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Workflow className="h-5 w-5" />
                  Temporal Workflows
                </CardTitle>
                <CardDescription>Durable workflow orchestration engine</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Web UI</p>
                  <code className="text-sm">http://localhost:8080</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">gRPC Endpoint</p>
                  <code className="text-sm">localhost:7233</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Namespace</p>
                  <code className="text-sm">default</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Task Queue</p>
                  <code className="text-sm">vdb-tasks</code>
                </div>
                <p className="pt-2 text-xs text-muted-foreground">
                  Click "Temporal" in the sidebar to view workflow executions and history.
                </p>
              </CardContent>
            </Card>

            {/* API Documentation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  API Documentation
                </CardTitle>
                <CardDescription>FastAPI with interactive Swagger UI</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Base URL</p>
                  <code className="text-sm">http://localhost:8000</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Swagger UI</p>
                  <code className="text-sm">http://localhost:8000/docs</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">ReDoc</p>
                  <code className="text-sm">http://localhost:8000/redoc</code>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">OpenAPI Schema</p>
                  <code className="text-sm">http://localhost:8000/openapi.json</code>
                </div>
                <p className="pt-2 text-xs text-muted-foreground">
                  Click "API Docs" in the sidebar to explore all available endpoints.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
