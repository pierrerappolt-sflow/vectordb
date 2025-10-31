"""Embedding value object."""

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
    """Immutable embedding vector."""

    chunk_id: ChunkId
    embedding_strategy_id: EmbeddingStrategyId
    vector: tuple[float, ...]

    library_id: LibraryId
    vectorization_config_id: VectorizationConfigId

    def __post_init__(self) -> None:
        if not self.vector or len(self.vector) == 0:
            raise ValidationException("Embedding vector cannot be empty")

    @property
    def embedding_id(self) -> EmbeddingId:
        return EmbeddingId.from_chunk_and_strategy(chunk_id=self.chunk_id, strategy_id=self.embedding_strategy_id)

    @property
    def dimensions(self) -> int:
        return len(self.vector)
