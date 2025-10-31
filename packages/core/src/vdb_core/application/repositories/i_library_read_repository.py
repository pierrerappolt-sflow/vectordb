"""Read repository interface for Library read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import LibraryReadModel


class ILibraryReadRepository(ABC):
    """Repository interface for Library read operations.

    Following CQRS:
    - Separate from write repository (ILibraryRepository)
    - Returns read models (DTOs), not domain entities
    - Optimized for reads (can use different storage, indexes, etc.)
    - No UoW tracking needed (read-only)

    Implementation notes:
    - Can read from same DB as writes (simple approach)
    - Can read from denormalized read store (advanced)
    - Can read from event store projections (event sourcing)
    """

    @abstractmethod
    async def get_by_id(self, library_id: str) -> LibraryReadModel:
        """Get library by ID.

        Args:
            library_id: Library ID (UUID string)

        Returns:
            LibraryReadModel if found

        Raises:
            LibraryNotFoundError: If library not found or deleted

        """

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[LibraryReadModel]:
        """Get all libraries with pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of LibraryReadModel instances

        """
