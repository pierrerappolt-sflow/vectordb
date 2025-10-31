"""Read repository interface for Document read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import DocumentReadModel


class IDocumentReadRepository(ABC):
    """Repository interface for Document read operations.

    Following CQRS:
    - Separate from write repository
    - Returns read models (DTOs), not domain entities
    - Optimized for reads
    - No UoW tracking needed (read-only)
    """

    @abstractmethod
    async def get_by_id(self, library_id: str, document_id: str) -> DocumentReadModel | None:
        """Get document by ID.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)

        Returns:
            DocumentReadModel if found, None otherwise

        """

    @abstractmethod
    async def get_all_in_library(self, library_id: str, limit: int = 100, offset: int = 0) -> list[DocumentReadModel]:
        """Get all documents in a library with pagination.

        Args:
            library_id: Library ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of DocumentReadModel instances

        """
