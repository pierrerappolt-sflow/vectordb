"""Read repository interface for Query read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import QueryReadModel


class IQueryReadRepository(ABC):
    """Repository interface for Query read operations.

    Following CQRS:
    - Separate from write repository
    - Returns read models (DTOs), not domain entities
    - Optimized for reads
    - No UoW tracking needed (read-only)
    """

    @abstractmethod
    async def get_by_id(self, library_id: str, query_id: str) -> QueryReadModel | None:
        """Get query by ID.

        Args:
            library_id: Library ID (UUID string)
            query_id: Query ID (UUID string)

        Returns:
            QueryReadModel if found, None otherwise

        """

    @abstractmethod
    async def get_all_in_library(self, library_id: str, limit: int = 100, offset: int = 0) -> list[QueryReadModel]:
        """Get all queries in a library with pagination.

        Args:
            library_id: Library ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of QueryReadModel instances ordered by created_at descending

        """
