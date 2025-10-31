"""Chunk value object - immutable content fragment within a Document.

Chunks are deduplicated within a library based on content hash.
Multiple documents can reference the same chunk.
"""

from __future__ import annotations

from dataclasses import field
from typing import TYPE_CHECKING

from pydantic.dataclasses import dataclass

from vdb_core.domain.value_objects.strategy import ChunkingStrategyId, ModalityType, ModalityTypeEnum

from .chunk_id import ChunkId

if TYPE_CHECKING:
    from uuid import UUID

    from vdb_core.domain.value_objects.common import ContentHash
    from vdb_core.domain.value_objects.library import LibraryId


@dataclass(frozen=True, kw_only=True)
class Chunk:
    """Immutable chunk content - scoped to document and chunking strategy.

    Chunks are value objects defined by their content, document, and strategy.
    The same content can be chunked differently by different strategies or
    appear in different documents.

    Natural composite key: (document_id, chunking_strategy_id, content_hash)

    Supports multiple modalities:
    - TEXT: content is str
    - IMAGE: content is bytes (JPEG/PNG/WebP)
    """

    library_id: LibraryId
    document_id: UUID
    modality: ModalityType
    content: str | bytes  # Type determined by modality
    chunking_strategy_id: ChunkingStrategyId
    content_hash: ContentHash
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate chunk invariants."""
        # Content type must match modality
        if self.modality.value == ModalityTypeEnum.TEXT:
            if not isinstance(self.content, str):
                msg = f"TEXT modality requires str content, got {type(self.content)}"
                raise TypeError(msg)
        # IMAGE uses bytes
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
        """Get content as text (only valid for TEXT modality).

        Returns:
            Text content

        Raises:
            TypeError: If modality is not TEXT

        """
        if self.modality.value != ModalityTypeEnum.TEXT:
            msg = f"Cannot get text_content for {self.modality.value} modality"
            raise TypeError(msg)
        return str(self.content)

    @property
    def binary_content(self) -> bytes:
        """Get content as bytes (for IMAGE modality).

        Returns:
            Binary content

        Raises:
            TypeError: If modality is TEXT

        """
        if self.modality.value == ModalityTypeEnum.TEXT:
            msg = "Cannot get binary_content for TEXT modality"
            raise TypeError(msg)
        # After check, content must be bytes (not str)
        assert isinstance(self.content, bytes)
        return self.content

    def to_embedding_format(self) -> str | bytes:
        """Convert content to format suitable for embedding models.

        Returns:
            - TEXT: str (the text itself)
            - IMAGE: bytes (will be base64-encoded by embedding service)

        """
        return self.content
