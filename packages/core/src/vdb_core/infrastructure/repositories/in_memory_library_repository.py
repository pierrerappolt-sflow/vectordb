"""In-memory implementation of Library repository for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from vdb_core.domain.repositories import AbstractRepository

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from vdb_core.domain.entities import Library
    from vdb_core.domain.value_objects import LibraryId


class InMemoryLibraryRepository(AbstractRepository["Library", "LibraryId"]):
    """In-memory implementation of Library repository.

    Following Cosmic Python's template method pattern:
    - Extends AbstractRepository for automatic `self.seen` tracking
    - Implements private methods (_add, _get, _update) for storage operations
    - Public methods (add, get, update) inherited from AbstractRepository

    Features:
    - Async streaming support (even though in-memory)
    - Thread-safe for concurrent access (dict operations are atomic in Python)
    """

    def __init__(self, shared_storage: dict[str, Library] | None = None) -> None:
        """Initialize repository with seen tracking.

        Args:
            shared_storage: Optional shared storage dict for CQRS consistency.
                          If provided, all repository instances share the same storage.
                          If None, creates a new isolated storage dict (for testing).

        """
        super().__init__()  # Get self.seen from AbstractRepository
        self._storage: dict[str, Library] = shared_storage if shared_storage is not None else {}

    async def _add(self, entity: Library) -> None:
        """Persist library to storage.

        Args:
            entity: The library to add

        Note:
            AbstractRepository.add() will track entity in self.seen automatically.

        """
        self._storage[str(entity.id)] = entity

    async def _get(self, id: LibraryId) -> Library | None:
        """Retrieve library from storage.

        Args:
            id: The library ID

        Returns:
            The library entity if found, None otherwise

        Note:
            AbstractRepository.get() will track entity in self.seen automatically.

        """
        return self._storage.get(str(id))

    async def _update(self, entity: Library) -> None:
        """Update library in storage.

        Args:
            entity: The library to update

        Raises:
            KeyError: If library doesn't exist

        Note:
            AbstractRepository.update() will track entity in self.seen automatically.

        """
        if str(entity.id) not in self._storage:
            msg = f"Library {entity.id} not found"
            raise KeyError(msg)

        self._storage[str(entity.id)] = entity

    async def _delete(self, id: LibraryId) -> None:
        """Hard delete a library by ID (removes from storage).

        Args:
            id: The library ID

        Raises:
            KeyError: If library doesn't exist

        """
        if str(id) not in self._storage:
            msg = f"Library {id} not found"
            raise KeyError(msg)

        del self._storage[str(id)]

    async def _soft_delete(self, entity: Library) -> None:
        """Soft delete a library (marks as DELETED).

        Args:
            entity: The library to soft delete

        Raises:
            KeyError: If library doesn't exist

        """
        from vdb_core.domain.value_objects import LibraryStatus

        if str(entity.id) not in self._storage:
            msg = f"Library {entity.id} not found"
            raise KeyError(msg)

        # Mark library as DELETED
        entity.status = LibraryStatus.DELETED
        self._storage[str(entity.id)] = entity

    async def stream(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> AsyncIterator[Library]:
        """Stream libraries for memory-efficient iteration.

        Even though this is in-memory, we implement streaming
        to match the interface of real repositories.

        Args:
            skip: Number of entities to skip
            limit: Maximum number to yield

        Yields:
            Libraries one at a time

        """
        libraries = list(self._storage.values())

        # Apply skip
        libraries = libraries[skip:]

        # Apply limit
        if limit is not None:
            libraries = libraries[:limit]

        # Yield one at a time (async generator)
        for library in libraries:
            yield library

    def clear(self) -> None:
        """Clear all data (useful for tests)."""
        self._storage.clear()
        self.seen.clear()
        self.added.clear()

    async def get_by_document_id(self, document_id: UUID) -> Library:
        """Get library that contains the specified document.

        Args:
            document_id: Document ID to search for

        Returns:
            Library containing the document

        Raises:
            ValueError: If no library contains this document

        """
        # Search through all libraries to find which one contains this document
        for library in self._storage.values():
            # Check if document exists in library's documents
            try:
                await library.get_document(document_id)
                return library
            except (KeyError, ValueError):
                # Document not in this library, continue searching
                continue

        msg = f"No library found containing document {document_id}"
        raise ValueError(msg)

    def __len__(self) -> int:
        """Get count of libraries in storage."""
        return len(self._storage)
