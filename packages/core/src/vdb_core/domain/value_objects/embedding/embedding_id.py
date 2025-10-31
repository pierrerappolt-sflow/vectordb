"""EmbeddingId value object - deterministic identifier for Embedding value objects."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, final

from pydantic.dataclasses import dataclass

from vdb_core.domain.value_objects.common import ContentHash

if TYPE_CHECKING:
    from vdb_core.domain.value_objects.chunk import ChunkId
    from vdb_core.domain.value_objects.strategy import EmbeddingStrategyId

# Namespace UUID for embedding IDs (different from chunks)
EMBEDDING_NAMESPACE_UUID = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")


@final
@dataclass(frozen=True, slots=True)
class EmbeddingId:
    """Value object representing an Embedding's deterministic identifier.

    Embeddings are deduplicated based on chunk + embedding strategy.
    Natural composite key: (chunk_id, embedding_strategy_id)

    Same chunk with different strategies = different embeddings
    Same chunk with same strategy = same embedding (deduplicated)

    ID is stored as UUID v5 (derived from SHA hash) for database compatibility.
    """

    value: str  # UUID string

    @classmethod
    def from_chunk_and_strategy(cls, chunk_id: ChunkId, strategy_id: EmbeddingStrategyId) -> EmbeddingId:
        """Generate deterministic EmbeddingId from chunk + strategy.

        This enables embedding deduplication:
        - Same chunk + strategy → same embedding_id (deduplicated)
        - Same chunk + different strategy → different embedding_ids

        Args:
            chunk_id: The chunk being embedded
            strategy_id: The embedding strategy being used

        Returns:
            Deterministic EmbeddingId based on chunk + strategy (as UUID v5)

        Example:
            # Same chunk, different strategies = different IDs
            id1 = EmbeddingId.from_chunk_and_strategy(chunk, strategy_a)
            id2 = EmbeddingId.from_chunk_and_strategy(chunk, strategy_b)
            assert id1 != id2

            # Same chunk + strategy = same ID (deduplication)
            id3 = EmbeddingId.from_chunk_and_strategy(chunk, strategy_a)
            assert id1 == id3

        """
        # Hash: chunk_id + strategy_id
        composite = f"{chunk_id}:{strategy_id}"
        content_hash = ContentHash.from_content(composite)

        # Convert SHA hash to UUID v5 for database compatibility
        embedding_uuid = uuid.uuid5(EMBEDDING_NAMESPACE_UUID, content_hash.value)
        return cls(value=str(embedding_uuid))
