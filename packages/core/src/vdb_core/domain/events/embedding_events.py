"""Embedding domain events."""

from dataclasses import dataclass

from vdb_core.domain.base import DomainEvent
from vdb_core.domain.value_objects import ChunkId, EmbeddingId, EmbeddingStrategyId, LibraryId


@dataclass(frozen=True)
class EmbeddingCreated(DomainEvent):
    """Event raised when an Embedding is created.

    This event is consumed by the search service to build in-memory vector indices.
    """

    embedding_id: EmbeddingId
    chunk_id: ChunkId
    library_id: LibraryId
    embedding_strategy_id: EmbeddingStrategyId
    vector: tuple[float, ...]  # The actual embedding vector
    dimensions: int  # Vector dimensionality
    vector_indexing_strategy: str  # FLAT, HNSW, IVF


@dataclass(frozen=True)
class EmbeddingDeleted(DomainEvent):
    """Event raised when an Embedding is deleted."""

    embedding_id: EmbeddingId
    chunk_id: ChunkId
