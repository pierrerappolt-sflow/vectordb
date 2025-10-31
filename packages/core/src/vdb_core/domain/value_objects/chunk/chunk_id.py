"""ChunkId value object - deterministic identifier for Chunk value objects."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, final

from pydantic.dataclasses import dataclass

from vdb_core.domain.value_objects.common import ContentHash

if TYPE_CHECKING:
    from uuid import UUID

    from vdb_core.domain.value_objects.library import LibraryId
    from vdb_core.domain.value_objects.strategy import ChunkingStrategyId

# Namespace UUID for chunk IDs (deterministic)
CHUNK_NAMESPACE_UUID = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


@final
@dataclass(frozen=True, slots=True)
class ChunkId:
    """Value object representing a Chunk's deterministic content-based identifier.

    Chunks are deduplicated within a library based on content hash.
    Natural composite key: (library_id, content_hash)

    Same content in different libraries = different chunk IDs
    Same content in same library = same chunk ID (deduplicated)

    ID is stored as UUID v5 (derived from SHA hash) for database compatibility.
    """

    value: str  # UUID string

    @classmethod
    def from_content(
        cls,
        library_id: LibraryId,
        document_id: UUID,
        chunking_strategy_id: ChunkingStrategyId,
        content: str | bytes,
    ) -> ChunkId:
        """Generate deterministic ChunkId from document + strategy + content.

        This enables proper scoping of chunks:
        - Same content in different documents → different chunk_ids
        - Same content with different strategies → different chunk_ids
        - Same content/document/strategy → same chunk_id (deduplicated)

        Args:
            library_id: Library this chunk belongs to
            document_id: Document this chunk belongs to
            chunking_strategy_id: Chunking strategy used to create this chunk
            content: The chunk content (text or bytes)

        Returns:
            Deterministic ChunkId scoped to document+strategy (as UUID v5)

        """
        # Convert bytes to string for hashing
        content_str = content.decode("utf-8") if isinstance(content, bytes) else content

        # Hash: library_id + document_id + chunking_strategy_id + content
        composite = f"{library_id}:{document_id}:{chunking_strategy_id}:{content_str}"
        content_hash = ContentHash.from_content(composite)

        # Convert SHA hash to UUID v5 for database compatibility
        chunk_uuid = uuid.uuid5(CHUNK_NAMESPACE_UUID, content_hash.value)
        return cls(value=str(chunk_uuid))
