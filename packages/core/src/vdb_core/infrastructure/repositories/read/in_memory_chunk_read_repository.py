"""In-memory implementation of Chunk read repository (CQRS read side)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import ChunkReadModel
from vdb_core.application.repositories import IChunkReadRepository
from vdb_core.domain.value_objects import ChunkId

if TYPE_CHECKING:
    from vdb_core.domain.entities import Library
    from vdb_core.domain.value_objects import Chunk


class InMemoryChunkReadRepository(IChunkReadRepository):
    """In-memory implementation of Chunk read repository.

    Following CQRS:
    - Read-only operations
    - Returns read models (DTOs), not domain entities
    - No UoW tracking (queries don't modify state)

    Implementation approach:
    - Shares storage reference with write repository (simple approach)
    - Converts domain entities to read models on the fly
    - Navigates through Library → Document → Chunks to access chunks
    """

    def __init__(self, library_storage: dict[str, Library]) -> None:
        """Initialize read repository.

        Args:
            library_storage: Reference to the write side library storage dict
                            (shared for simplicity in in-memory implementation)

        Note:
            Chunks are accessed through their parent Library → Document aggregate.

        """
        self._library_storage = library_storage

    async def _get_chunk_text(self, chunk: Chunk) -> str:
        """Get chunk text content.

        Args:
            chunk: Domain entity

        Returns:
            Chunk text, or empty string if text loader not configured

        """
        if chunk._text_loader:  # type: ignore[attr-defined]
            return await chunk._text_loader()  # type: ignore[attr-defined,no-any-return]
        return ""

    async def _to_read_model(self, chunk: Chunk) -> ChunkReadModel:
        """Convert domain entity to read model.

        Args:
            chunk: Domain entity

        Returns:
            Read model DTO

        """
        # Get text content (may be lazy loaded)
        text = await self._get_chunk_text(chunk)

        return ChunkReadModel(
            id=str(chunk.id),  # type: ignore[attr-defined]
            document_id=str(chunk.document_id),  # type: ignore[attr-defined]
            chunking_strategy=chunk.chunking_strategy.value,  # type: ignore[attr-defined]
            text=text,
            status=chunk.status,  # type: ignore[attr-defined]
            metadata=chunk.metadata,
            created_at=chunk.created_at,  # type: ignore[attr-defined]
            updated_at=chunk.updated_at,  # type: ignore[attr-defined]
        )

    async def get_by_id(self, chunk_id: ChunkId) -> ChunkReadModel | None:
        """Get a chunk by its ID.

        Args:
            chunk_id: Chunk ID value object

        Returns:
            ChunkReadModel if found, None otherwise

        """
        # Search through all libraries → documents → chunks
        for library in self._library_storage.values():
            for document in library._documents.values():
                if chunk_id in document._chunks:
                    chunk = document._chunks[chunk_id]
                    return await self._to_read_model(chunk)

        return None

    async def get_chunks_by_document(
        self, library_id: str, document_id: str, limit: int = 100, offset: int = 0
    ) -> list[ChunkReadModel]:
        """Get all chunks for a document with pagination.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of ChunkReadModel instances ordered by start index

        """
        # Get library from storage
        library = self._library_storage.get(library_id)
        if not library:
            return []

        # Find document in library
        document = None
        for doc in library._documents.values():
            if str(doc.id) == document_id:
                document = doc
                break

        if not document:
            return []

        # Get chunks from document (dict values)
        chunks = list(document._chunks.values())

        # Apply pagination
        chunks = chunks[offset : offset + limit]

        # Convert to read models (need to await since _to_read_model is async)
        read_models = []
        for chunk in chunks:
            read_models.append(await self._to_read_model(chunk))

        return read_models
