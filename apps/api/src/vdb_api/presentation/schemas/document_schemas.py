"""Document API schemas."""

from pydantic import BaseModel, Field

from vdb_api.presentation.schemas.library_schemas import DocumentVectorizationStatusResponse


class DocumentFragmentResponse(BaseModel):
    """Response for a single document fragment."""

    id: str = Field(..., description="Fragment ID (UUID)")
    document_id: str = Field(..., description="Parent document ID (UUID)")
    sequence_number: int = Field(..., description="Fragment order (0-based)")
    size_bytes: int = Field(..., description="Fragment size in bytes")
    content: str = Field(..., description="Fragment text content")
    content_hash: str = Field(..., description="SHA1 hash of content")
    is_final: bool = Field(..., description="Whether this is the final fragment")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")


class DocumentResponse(BaseModel):
    """Document response model."""

    id: str = Field(..., description="Document ID (UUID)")
    library_id: str = Field(..., description="Parent library ID (UUID)")
    name: str = Field(..., description="Document filename")
    status: str = Field(..., description="Document status")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")
    upload_complete: bool = Field(..., description="Whether upload is complete")
    fragment_count: int = Field(..., description="Number of fragments")
    total_bytes: int = Field(..., description="Total bytes across all fragments")
    embeddings_count: int = Field(0, description="Total embeddings created for this document (all configs)")
    embeddings_by_config_id: dict[str, int] = Field(
        default_factory=dict, description="Embeddings count per vectorization config ID"
    )
    vectorization_statuses: list[DocumentVectorizationStatusResponse] = Field(
        default_factory=list, description="Vectorization processing status per config"
    )
    fragments: list[DocumentFragmentResponse] = Field(
        default_factory=list, description="Document fragments (raw content)"
    )


class GetDocumentsResponse(BaseModel):
    """Response with list of documents."""

    documents: list[DocumentResponse]
    total: int = Field(..., description="Total number of documents")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    document_id: str = Field(..., description="Document ID (UUID)")
    library_id: str = Field(..., description="Library ID (UUID)")
    filename: str = Field(..., description="Document filename")
    fragments_received: int = Field(..., description="Number of fragments received")
    total_bytes: int = Field(..., description="Total bytes uploaded")
    upload_complete: bool = Field(..., description="Whether upload is complete")
    message: str = Field(default="Document uploaded successfully")


class ChunkResponse(BaseModel):
    """Response for a single chunk."""

    id: str = Field(..., description="Chunk ID (deterministic hash)")
    document_id: str = Field(..., description="Parent document ID (UUID)")
    chunking_strategy: str = Field(..., description="Chunking strategy used")
    text: str = Field(..., description="Chunk text content")
    status: str = Field(..., description="Chunk status")
    metadata: dict[str, object] = Field(default_factory=dict, description="Additional metadata")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")


class GetDocumentChunksResponse(BaseModel):
    """Response with list of document chunks."""

    chunks: list[ChunkResponse]
    total: int = Field(..., description="Total number of chunks")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")


class ChunkWithContextResponse(BaseModel):
    """Response for a chunk with surrounding context."""

    chunk: ChunkResponse = Field(..., description="The requested chunk")
    chunks_before: list[ChunkResponse] = Field(default_factory=list, description="Chunks before the requested chunk")
    chunks_after: list[ChunkResponse] = Field(default_factory=list, description="Chunks after the requested chunk")
    document: DocumentResponse = Field(..., description="Parent document metadata")
    total_chunks_in_document: int = Field(..., description="Total chunks in this document")
