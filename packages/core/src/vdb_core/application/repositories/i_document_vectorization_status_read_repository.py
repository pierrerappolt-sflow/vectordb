"""Read repository interface for DocumentVectorizationStatus read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import DocumentVectorizationStatusReadModel


class IDocumentVectorizationStatusReadRepository(ABC):
    """Repository interface for DocumentVectorizationStatus read operations.

    Following CQRS:
    - Separate from write repository
    - Returns read models (DTOs), not domain entities
    - Optimized for reads (can use different storage, indexes, etc.)
    - No UoW tracking needed (read-only)

    Implementation notes:
    - Reads from document_vectorization_status table
    - Returns processing status for each document+config pair
    - Shows PENDING/PROCESSING/COMPLETED/FAILED status
    """

    @abstractmethod
    async def get_by_document(
        self, library_id: str, document_id: str
    ) -> list[DocumentVectorizationStatusReadModel]:
        """Get all vectorization status entries for a document.

        Returns the processing status for each VectorizationConfig
        that this document is being processed with.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)

        Returns:
            List of DocumentVectorizationStatusReadModel instances

        """
