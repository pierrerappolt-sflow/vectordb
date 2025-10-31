"""Library repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from vdb_core.domain.base import AbstractRepository
from vdb_core.domain.entities import Library
from vdb_core.domain.value_objects import DocumentId, LibraryId


class ILibraryRepository(AbstractRepository[Library, LibraryId], ABC):
    """Repository for Library aggregate root.

    Inherits standard CRUD operations and automatic `seen` tracking from AbstractRepository.
    Add library-specific query methods here as needed.
    """

    @abstractmethod
    async def get_by_document_id(self, document_id: DocumentId) -> Library:
        """Get library that contains the specified document.

        Args:
            document_id: Document ID to search for

        Returns:
            Library containing the document

        Raises:
            LibraryNotFoundError: If no library contains this document

        """
        ...
