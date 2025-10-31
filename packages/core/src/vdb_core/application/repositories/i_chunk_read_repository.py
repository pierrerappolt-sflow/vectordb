"""Read repository interface for Chunk read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import ChunkReadModel
from vdb_core.domain.value_objects import ChunkId


class IChunkReadRepository(ABC):
    """Repository interface for Chunk read operations.

    Following CQRS:
    - Separate from write repository
    - Returns read models (DTOs), not domain entities
    - Optimized for reads
    - No UoW tracking needed (read-only)
    """

    @abstractmethod
    async def get_by_id(self, chunk_id: ChunkId) -> ChunkReadModel | None:
        """Get a chunk by its ID.

        Args:
            chunk_id: Chunk ID value object

        Returns:
            ChunkReadModel if found, None otherwise

        """

    @abstractmethod
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
            List of ChunkReadModel instances

        """
