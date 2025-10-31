"""In-memory implementation of Document read repository (CQRS read side)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import DocumentReadModel
from vdb_core.application.repositories import IDocumentReadRepository

if TYPE_CHECKING:
    from vdb_core.domain.entities import Document, Library


class InMemoryDocumentReadRepository(IDocumentReadRepository):
    """In-memory implementation of Document read repository.

    Following CQRS:
    - Read-only operations
    - Returns read models (DTOs), not domain entities
    - No UoW tracking (queries don't modify state)

    Implementation approach:
    - Shares storage reference with write repository (simple approach)
    - Converts domain entities to read models on the fly
    - Navigates through Library aggregate to access Documents
    """

    def __init__(self, library_storage: dict[str, Library]) -> None:
        """Initialize read repository.

        Args:
            library_storage: Reference to the write side library storage dict
                            (shared for simplicity in in-memory implementation)

        Note:
            Documents are accessed through their parent Library aggregate.

        """
        self._library_storage = library_storage

    def _calculate_total_bytes(self, document: Document) -> int:
        """Calculate total bytes across all fragments.

        Args:
            document: Domain entity

        Returns:
            Total bytes in all fragments

        """
        total = 0
        for fragment in document._fragments.cached_items:
            total += len(fragment.content)
        return total

    def _calculate_embeddings_count(self, document: Document) -> int:
        """Calculate total embeddings created for this document.

        Args:
            document: Domain entity

        Returns:
            Total embeddings count across all configs

        Note:
            For in-memory implementation, we would need to access the library's
            embeddings through chunks. For simplicity, we return 0 here.
            Production uses PostgreSQL which efficiently counts embeddings.

        """
        # In-memory implementation: would need access to library.embeddings
        # For simplicity, return 0 (this is mainly for testing anyway)
        return 0

    def _to_read_model(self, document: Document) -> DocumentReadModel:
        """Convert domain entity to read model.

        Args:
            document: Domain entity

        Returns:
            Read model DTO

        """
        return DocumentReadModel(
            id=str(document.id),
            library_id=str(document.library_id),
            name=document.name.value,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
            upload_complete=document.upload_complete,
            fragment_count=len(document._fragments.cached_items),  # Denormalized
            total_bytes=self._calculate_total_bytes(document),  # Denormalized
            embeddings_count=self._calculate_embeddings_count(document),  # Denormalized
            embeddings_by_config_id={},  # In-memory implementation returns empty for simplicity
        )

    async def get_by_id(self, library_id: str, document_id: str) -> DocumentReadModel | None:
        """Get document by ID.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)

        Returns:
            DocumentReadModel if found, None otherwise

        """
        # Get library from storage
        library = self._library_storage.get(library_id)
        if not library:
            return None

        # Find document in library's documents (iterate over values, not keys)
        for document in library._documents.values():
            if str(document.id) == document_id:
                return self._to_read_model(document)

        return None

    async def get_all_in_library(self, library_id: str, limit: int = 100, offset: int = 0) -> list[DocumentReadModel]:
        """Get all documents in a library with pagination.

        Args:
            library_id: Library ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of DocumentReadModel instances

        """
        # Get library from storage
        library = self._library_storage.get(library_id)
        if not library:
            return []

        # Get documents from library (dict values, not keys)
        documents = list(library._documents.values())

        # Apply pagination
        documents = documents[offset : offset + limit]

        # Convert to read models
        return [self._to_read_model(doc) for doc in documents]
