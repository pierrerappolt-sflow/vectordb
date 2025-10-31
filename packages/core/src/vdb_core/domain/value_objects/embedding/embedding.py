"""Embedding value object - immutable vector representation of chunk content."""

from __future__ import annotations

from pydantic.dataclasses import dataclass

from vdb_core.domain.exceptions import ValidationException
from vdb_core.domain.value_objects.chunk import ChunkId
from vdb_core.domain.value_objects.config import VectorizationConfigId
from vdb_core.domain.value_objects.library import LibraryId
from vdb_core.domain.value_objects.strategy import EmbeddingStrategyId

from .embedding_id import EmbeddingId


@dataclass(frozen=True, kw_only=True)
class Embedding:
    """Immutable embedding vector - deduplicated by chunk + strategy.

    Embeddings are value objects stored once and referenced by multiple
    documents that share the same chunk content.

    Natural composite key: (chunk_id, embedding_strategy_id)

    One chunk can have multiple embeddings (different strategies),
    but same chunk + same strategy = same embedding (deduplicated).

    Example:
        Chunk "Hello world" with strategy "cohere-english-v3":
        - Stored once as Embedding(chunk_id, strategy_id, vector)
        - Multiple documents can reference the same chunk
        - Both documents share the same embedding

    """

    chunk_id: ChunkId
    embedding_strategy_id: EmbeddingStrategyId
    vector: tuple[float, ...]

    # Query context (not part of natural key, but needed for filtering)
    library_id: LibraryId
    vectorization_config_id: VectorizationConfigId

    def __post_init__(self) -> None:
        """Validate embedding vector."""
        if not self.vector:
            msg = "Embedding vector cannot be empty"
            raise ValidationException(msg)

        if len(self.vector) == 0:
            msg = "Embedding vector must have at least one dimension"
            raise ValidationException(msg)

    @property
    def embedding_id(self) -> EmbeddingId:
        """Computed natural key for this embedding."""
        return EmbeddingId.from_chunk_and_strategy(chunk_id=self.chunk_id, strategy_id=self.embedding_strategy_id)

    @property
    def dimensions(self) -> int:
        """Return the dimensionality of the embedding."""
        return len(self.vector)
