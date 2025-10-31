"""Chunk value object."""

from __future__ import annotations

from dataclasses import field
from uuid import UUID

from pydantic.dataclasses import dataclass

from vdb_core.domain.value_objects.strategy import ChunkingStrategyId, ModalityType
from vdb_core.domain.value_objects.common import ContentHash
from vdb_core.domain.value_objects.library import LibraryId

from .chunk_id import ChunkId


@dataclass(frozen=True, kw_only=True)
class Chunk:
    """Immutable chunk content."""

    library_id: LibraryId
    document_id: "UUID"
    modality: ModalityType
    content: str | bytes  # Type determined by modality
    chunking_strategy_id: ChunkingStrategyId
    content_hash: ContentHash
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate chunk invariants."""
        if self.modality == ModalityType.TEXT:
            if not isinstance(self.content, str):
                msg = f"TEXT modality requires str content, got {type(self.content)}"
                raise TypeError(msg)
        elif not isinstance(self.content, bytes):
            msg = f"{self.modality.value} modality requires bytes content, got {type(self.content)}"
            raise TypeError(msg)

    @property
    def chunk_id(self) -> ChunkId:
        """Computed natural key for this chunk."""
        return ChunkId.from_content(
            library_id=self.library_id,
            document_id=self.document_id,
            chunking_strategy_id=self.chunking_strategy_id,
            content=self.content,
        )

    @property
    def text_content(self) -> str:
        """Get content as text (TEXT modality)."""
        if self.modality != ModalityType.TEXT:
            msg = f"Cannot get text_content for {self.modality.value} modality"
            raise TypeError(msg)
        return str(self.content)

    @property
    def binary_content(self) -> bytes:
        """Get content as bytes (non-TEXT)."""
        if self.modality == ModalityType.TEXT:
            msg = "Cannot get binary_content for TEXT modality"
            raise TypeError(msg)
        assert isinstance(self.content, bytes)
        return self.content

    def to_embedding_format(self) -> str | bytes:
        """Return content for embedding models."""
        return self.content
