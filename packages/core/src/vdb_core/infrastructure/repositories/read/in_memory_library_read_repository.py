"""In-memory implementation of Library read repository (CQRS read side)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import LibraryReadModel
from vdb_core.application.repositories import ILibraryReadRepository

if TYPE_CHECKING:
    from vdb_core.domain.entities import Library


class InMemoryLibraryReadRepository(ILibraryReadRepository):
    """In-memory implementation of Library read repository.

    Following CQRS:
    - Read-only operations
    - Returns read models (DTOs), not domain entities
    - No UoW tracking (queries don't modify state)

    Implementation approach:
    - Shares storage reference with write repository (simple approach)
    - Converts domain entities to read models on the fly
    - In production, could read from separate denormalized store
    """

    def __init__(self, write_storage: dict[str, Library]) -> None:
        """Initialize read repository.

        Args:
            write_storage: Reference to the write side storage dict
                          (shared for simplicity in in-memory implementation)

        Note:
            In production with real DB, read repo would use its own
            connection/session, possibly to a read replica or read model store.

        """
        self._storage = write_storage

    def _to_read_model(self, library: Library) -> LibraryReadModel:
        """Convert domain entity to read model.

        Args:
            library: Domain entity

        Returns:
            Read model DTO

        """
        return LibraryReadModel(
            id=str(library.id),
            name=library.name.value,
            status=library.status,
            created_at=library.created_at,
            updated_at=library.updated_at,
            document_count=len(library._documents),  # Denormalized for performance
        )

    async def get_by_id(self, library_id: str) -> LibraryReadModel:
        """Get library by ID (excludes DELETED libraries).

        Args:
            library_id: Library ID (UUID string)

        Returns:
            LibraryReadModel if found and not deleted

        Raises:
            LibraryNotFoundError: If library not found or deleted

        """
        from vdb_core.domain.exceptions import LibraryNotFoundError
        from vdb_core.domain.value_objects import LibraryStatus

        library = self._storage.get(library_id)
        if not library or library.status == LibraryStatus.DELETED:
            raise LibraryNotFoundError(library_id)
        return self._to_read_model(library)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[LibraryReadModel]:
        """Get all libraries with pagination (excludes DELETED libraries).

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of LibraryReadModel instances (excluding deleted)

        """
        from vdb_core.domain.value_objects import LibraryStatus

        # Filter out deleted libraries
        libraries = [lib for lib in self._storage.values() if lib.status != LibraryStatus.DELETED]

        # Apply pagination
        libraries = libraries[offset : offset + limit]

        # Convert to read models
        return [self._to_read_model(lib) for lib in libraries]
