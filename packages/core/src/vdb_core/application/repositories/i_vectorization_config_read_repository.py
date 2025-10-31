"""Read repository interface for VectorizationConfig read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import VectorizationConfigReadModel


class IVectorizationConfigReadRepository(ABC):
    """Repository interface for VectorizationConfig read operations.

    Following CQRS:
    - Separate from write repository (IVectorizationConfigRepository)
    - Returns read models (DTOs), not domain entities
    - Optimized for reads (can use different storage, indexes, etc.)
    - No UoW tracking needed (read-only)

    Implementation notes:
    - Reads from vectorization_configs table
    - Filters by status (ACTIVE, DEPRECATED)
    - Supports pagination for large result sets
    """

    @abstractmethod
    async def get_by_id(self, config_id: str) -> VectorizationConfigReadModel | None:
        """Get vectorization config by ID.

        Args:
            config_id: Config ID (UUID string)

        Returns:
            VectorizationConfigReadModel if found, None otherwise

        """

    @abstractmethod
    async def get_all(
        self, limit: int = 100, offset: int = 0, statuses: list[str] | None = None
    ) -> list[VectorizationConfigReadModel]:
        """Get all vectorization configs with pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            statuses: Filter by status values (default: ['ACTIVE', 'DEPRECATED'])

        Returns:
            List of VectorizationConfigReadModel instances

        """

    @abstractmethod
    async def count(self, statuses: list[str] | None = None) -> int:
        """Count total vectorization configs.

        Args:
            statuses: Filter by status values (default: ['ACTIVE', 'DEPRECATED'])

        Returns:
            Total count of configs matching filters

        """

    @abstractmethod
    async def get_by_library(self, library_id: str) -> list[VectorizationConfigReadModel]:
        """Get all vectorization configs associated with a library.

        Args:
            library_id: Library ID (UUID string)

        Returns:
            List of VectorizationConfigReadModel instances associated with the library

        """
