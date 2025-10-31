"""Read repository interface for Chunk value objects (query-only)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vdb_core.domain.value_objects import Chunk, ChunkId, LibraryId


class IChunkReadRepository(ABC):
    """Read-only repository for querying Chunk value objects.

    This is a CQRS read model - chunks are written through Library aggregate,
    read through this query interface.

    Example queries:
        # Get chunk by ID
        chunk = await chunk_read_repo.get_by_id(chunk_id)

        # Get all chunks in library
        chunks = await chunk_read_repo.get_by_library(library_id)
    """

    @abstractmethod
    async def get_by_id(self, chunk_id: ChunkId) -> Chunk | None:
        """Get chunk by ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Chunk if found, None otherwise

        """

    @abstractmethod
    async def get_by_library(self, library_id: LibraryId) -> list[Chunk]:
        """Get all chunks for a library.

        Args:
            library_id: Library identifier

        Returns:
            List of chunks in the library

        """

    @abstractmethod
    async def exists(self, chunk_id: ChunkId) -> bool:
        """Check if chunk exists.

        Args:
            chunk_id: Chunk identifier

        Returns:
            True if chunk exists, False otherwise

        """
