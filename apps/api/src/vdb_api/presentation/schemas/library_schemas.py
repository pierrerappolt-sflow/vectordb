"""Library API schemas."""

from pydantic import BaseModel, Field


class CreateLibraryRequest(BaseModel):
    """Request to create a new library."""

    name: str = Field(..., min_length=1, max_length=255, description="Library name")


class LibraryResponse(BaseModel):
    """Library response model."""

    id: str = Field(..., description="Library ID (UUID)")
    name: str = Field(..., description="Library name")
    status: str = Field(..., description="Library status (ACTIVE, ARCHIVED, etc.)")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")
    document_count: int = Field(..., description="Number of documents in library")


class CreateLibraryResponse(BaseModel):
    """Response after creating a library."""

    library: LibraryResponse
    message: str = Field(default="Library created successfully")


class GetLibrariesResponse(BaseModel):
    """Response with list of libraries."""

    libraries: list[LibraryResponse]
    total: int = Field(..., description="Total number of libraries")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")


class SearchLibraryRequest(BaseModel):
    """Request to search for similar content in a library."""

    query: str = Field(..., min_length=1, max_length=10000, description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of top results to return")


class SearchResult(BaseModel):
    """Single search result with chunk information."""

    chunk_id: str = Field(..., description="Chunk ID")
    embedding_id: str = Field(..., description="Embedding ID")
    document_id: str = Field(..., description="Document ID")
    similarity_score: float = Field(..., description="Cosine similarity score (-1.0 to 1.0)")
    text: str = Field(..., description="Chunk text content")


class SearchLibraryResponse(BaseModel):
    """Response with search results."""

    results: list[SearchResult] = Field(..., description="Search results sorted by similarity")
    query: str = Field(..., description="Original query text")
    total_results: int = Field(..., description="Number of results returned")
    library_id: str = Field(..., description="Library ID that was searched")


class CreateQueryRequest(BaseModel):
    """Request to create an async query for semantic search."""

    query: str = Field(..., min_length=1, max_length=10000, description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of top results to return")
    config_id: str = Field(..., description="Vectorization config ID to use for search")


class CreateQueryResponse(BaseModel):
    """Response after creating an async query."""

    query_id: str = Field(..., description="Query ID (UUID)")
    library_id: str = Field(..., description="Library ID being queried")
    status: str = Field(..., description="Query status (PENDING, PROCESSING, COMPLETED, FAILED)")
    message: str = Field(default="Query created and processing")


class QueryResponse(BaseModel):
    """Response with async query status and results."""

    query_id: str = Field(..., description="Query ID (UUID)")
    library_id: str = Field(..., description="Library ID that was queried")
    query_text: str = Field(..., description="Original query text")
    status: str = Field(..., description="Query status (PENDING, PROCESSING, COMPLETED, FAILED)")
    results: list[SearchResult] | None = Field(None, description="Search results (only when COMPLETED)")
    total_results: int = Field(0, description="Number of results returned")
    created_at: str = Field(..., description="ISO 8601 timestamp when query was created")
    completed_at: str | None = Field(None, description="ISO 8601 timestamp when query completed")


class GetQueriesResponse(BaseModel):
    """Response with list of queries for a library."""

    queries: list[QueryResponse] = Field(..., description="List of queries")
    total: int = Field(..., description="Total number of queries")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")


class EventLogResponse(BaseModel):
    """Event log response model."""

    id: str = Field(..., description="Event log ID (UUID)")
    event_type: str = Field(..., description="Type of event (e.g., DocumentCreated, ChunkProcessed)")
    aggregate_id: str = Field(..., description="ID of the aggregate that triggered the event")
    aggregate_type: str = Field(..., description="Type of aggregate (e.g., Document, Chunk)")
    payload: dict[str, object] = Field(..., description="Event payload with details")
    occurred_at: str = Field(..., description="ISO 8601 timestamp when event occurred")
    created_at: str = Field(..., description="ISO 8601 timestamp when event was logged")


class GetEventLogsResponse(BaseModel):
    """Response with list of event logs for a library."""

    events: list[EventLogResponse] = Field(..., description="List of event logs")
    total: int = Field(..., description="Total number of events matching filters")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")


class VectorizationConfigResponse(BaseModel):
    """Vectorization config response model."""

    id: str = Field(..., description="Config ID (UUID)")
    version: int = Field(..., description="Config version number")
    status: str = Field(..., description="Config status")
    description: str | None = Field(None, description="Config description")
    previous_version_id: str | None = Field(None, description="Previous version ID (if this is a new version)")
    chunking_strategy_ids: list[str] = Field(..., description="List of chunking strategy IDs")
    embedding_strategy_ids: list[str] = Field(..., description="List of embedding strategy IDs")
    chunking_strategy_names: list[str] = Field(default_factory=list, description="List of chunking strategy names")
    embedding_strategy_names: list[str] = Field(default_factory=list, description="List of embedding strategy names")
    vector_indexing_strategy: str = Field(..., description="Vector indexing strategy")
    vector_similarity_metric: str = Field(..., description="Similarity metric")


class GetVectorizationConfigsResponse(BaseModel):
    """Response with list of vectorization configs."""

    configs: list[VectorizationConfigResponse] = Field(..., description="List of configs")
    total: int = Field(..., description="Total number of configs")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")


class AddConfigToLibraryRequest(BaseModel):
    """Request to add a vectorization config to a library."""

    config_id: str = Field(..., description="Config ID (UUID)")


class AddConfigToLibraryResponse(BaseModel):
    """Response after adding a config to a library."""

    library_id: str = Field(..., description="Library ID")
    config_id: str = Field(..., description="Config ID")
    message: str = Field(default="Config added to library successfully")


class GetLibraryConfigsResponse(BaseModel):
    """Response with list of configs associated with a library."""

    library_id: str = Field(..., description="Library ID")
    configs: list[VectorizationConfigResponse] = Field(..., description="List of configs")
    total: int = Field(..., description="Total number of configs")


class DocumentVectorizationStatusResponse(BaseModel):
    """Status of document processing with a specific config."""

    document_id: str = Field(..., description="Document ID (UUID)")
    config_id: str = Field(..., description="Config ID (UUID)")
    status: str = Field(..., description="Processing status (PENDING, PROCESSING, COMPLETED, FAILED)")
    error_message: str | None = Field(None, description="Error message if status is FAILED")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")
