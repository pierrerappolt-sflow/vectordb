"""Read repository interface for DocumentFragment read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import DocumentFragmentReadModel


class IDocumentFragmentReadRepository(ABC):
    """Repository interface for DocumentFragment read operations.

    Following CQRS:
    - Separate from write repository
    - Returns read models (DTOs), not domain entities
    - Optimized for reads
    - No UoW tracking needed (read-only)
    """

    @abstractmethod
    async def get_all_in_document(
        self,
        library_id: str,
        document_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DocumentFragmentReadModel]:
        """Get all fragments for a document with pagination.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of DocumentFragmentReadModel instances ordered by sequence_number

        """
