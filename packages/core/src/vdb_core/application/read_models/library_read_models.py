"""Read models for Library queries (CQRS pattern)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LibraryReadModel:
    """Read model for Library query results.

    This is a simple DTO optimized for reads, separate from the
    domain entity. It contains only the data needed for queries.

    Following CQRS:
    - Read models are independent of domain entities
    - Optimized for query performance
    - Can be denormalized if needed
    - No business logic
    """

    id: str  # UUID as string
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0  # Denormalized for performance


@dataclass(frozen=True)
class DocumentReadModel:
    """Read model for Document query results.

    Following CQRS:
    - Separate from domain entity
    - Optimized for query performance
    - Denormalized data for efficient reads
    """

    id: str  # UUID as string
    library_id: str  # Parent library UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    upload_complete: bool
    fragment_count: int = 0  # Denormalized for performance
    total_bytes: int = 0  # Denormalized for performance
    embeddings_count: int = 0  # Total embeddings created for this document (backward compatibility)
    embeddings_by_config_id: dict[str, int] = None  # type: ignore[assignment]  # Embeddings count per config ID
    vectorization_statuses: list["DocumentVectorizationStatusReadModel"] = None  # type: ignore[assignment]
    fragments: list["DocumentFragmentReadModel"] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Initialize default values for mutable fields."""
        if self.embeddings_by_config_id is None:
            object.__setattr__(self, "embeddings_by_config_id", {})
        if self.vectorization_statuses is None:
            object.__setattr__(self, "vectorization_statuses", [])
        if self.fragments is None:
            object.__setattr__(self, "fragments", [])


@dataclass(frozen=True)
class DocumentFragmentReadModel:
    """Read model for DocumentFragment query results.

    Following CQRS:
    - Separate from domain entity
    - Optimized for query performance
    - Contains fragment content for display
    """

    id: str  # UUID as string
    document_id: str  # Parent document UUID
    sequence_number: int  # Fragment sequence number
    size_bytes: int  # Content size in bytes
    content: str  # Decoded text content
    content_hash: str  # SHA1 hash of content
    is_final: bool  # Is this the last fragment?
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ChunkReadModel:
    """Read model for Chunk query results.

    Following CQRS:
    - Separate from domain entity
    - Optimized for query performance
    - Contains chunk metadata and text content
    """

    id: str  # Deterministic chunk ID (sha1 hash)
    document_id: str  # Parent document UUID
    chunking_strategy: str  # ChunkingStrategy enum value
    text: str  # Chunk text content
    status: str  # ChunkStatus enum value
    metadata: dict[str, object]  # Additional metadata
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class VectorizationConfigReadModel:
    """Read model for VectorizationConfig query results.

    Following CQRS:
    - Separate from domain entity
    - Optimized for query performance
    - Contains config metadata for display
    """

    id: str  # UUID as string
    version: int  # Config version number
    status: str  # ConfigStatus enum value (ACTIVE, DEPRECATED, etc.)
    description: str | None  # Human-readable description
    previous_version_id: str | None  # Previous version UUID (if exists)
    chunking_strategy_ids: list[str]  # List of chunking strategy UUIDs
    embedding_strategy_ids: list[str]  # List of embedding strategy UUIDs
    vector_indexing_strategy: str  # VectorIndexingStrategy enum value
    vector_similarity_metric: str  # VectorSimilarityMetric enum value
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DocumentVectorizationStatusReadModel:
    """Read model for DocumentVectorizationStatus query results.

    Following CQRS:
    - Tracks processing status for document+config pairs
    - Optimized for query performance
    - Shows PENDING/PROCESSING/COMPLETED/FAILED status
    """

    id: str  # UUID as string
    document_id: str  # Parent document UUID
    config_id: str  # Vectorization config UUID
    status: str  # Processing status: pending, processing, completed, failed
    error_message: str | None  # Error details if status is failed
    created_at: datetime
    updated_at: datetime
