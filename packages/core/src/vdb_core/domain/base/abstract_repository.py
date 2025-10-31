"""Generic repository base class for domain entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from vdb_core.domain.entities import IEntity


class AbstractRepository[TEntity: "IEntity", TId](ABC):
    """Base repository implementation with automatic `seen` tracking.

    Following Cosmic Python's template method pattern:
    - Public methods (add, get, update) handle `self.seen` tracking
    - Private methods (_add, _get, _update) do actual database work
    - Subclasses only implement private methods

    Type Parameters:
        TEntity: The entity type managed by this repository
        TId: The ID type for the entity

    Example:
        class InMemoryLibraryRepository(AbstractRepository[Library, LibraryId]):
            def __init__(self):
                super().__init__()  # Get self.seen
                self._entities = {}

            async def _add(self, entity: Library) -> None:
                self._entities[entity.id] = entity

            async def _get(self, id: LibraryId) -> Library | None:
                return self._entities.get(id)

    """

    def __init__(self) -> None:
        """Initialize repository with empty seen set."""
        self.seen: set[TEntity] = set()
        self.added: set[TEntity] = set()  # Track newly added entities separately

    async def add(self, entity: TEntity) -> None:
        """Add entity and track in added set.

        Args:
            entity: The entity to add

        """
        await self._add(entity)
        self.seen.add(entity)
        self.added.add(entity)  # Track as newly added

    async def get(self, id: TId) -> TEntity:
        """Get entity and track in seen set if found.

        Args:
            id: The entity's unique identifier

        Returns:
            The entity

        Raises:
            EntityNotFoundError: If entity doesn't exist

        """
        entity = await self._get(id)
        if entity is None:
            from vdb_core.domain.exceptions import EntityNotFoundError
            raise EntityNotFoundError(f"Entity with id {id} not found")
        self.seen.add(entity)
        return entity

    async def update(self, entity: TEntity) -> None:
        """Update entity and track in seen set.

        Args:
            entity: The entity to update

        """
        await self._update(entity)
        self.seen.add(entity)

    async def delete(self, id: TId) -> None:
        """Hard delete entity (doesn't track in seen since entity is removed).

        Args:
            id: The entity's unique identifier

        """
        await self._delete(id)

    async def soft_delete(self, id: TId) -> None:
        """Soft delete entity (loads entity and tracks in seen).

        Args:
            id: The entity's unique identifier

        """
        entity = await self.get(id)
        await self._soft_delete(entity)
        self.seen.add(entity)

    @abstractmethod
    async def _add(self, entity: TEntity) -> None:
        """Persist the entity (implemented by subclasses).

        Args:
            entity: The entity to add

        Raises:
            ValidationException: If entity validation fails
            TransactionError: If persistence fails

        """
        ...

    @abstractmethod
    async def _get(self, id: TId) -> TEntity | None:
        """Retrieve entity by ID (implemented by subclasses).

        Args:
            id: The entity's unique identifier

        Returns:
            The entity if found, None otherwise

        Note:
            Implementations should return None if not found.
            The public get() method will raise EntityNotFoundError.

        """
        ...

    @abstractmethod
    async def _update(self, entity: TEntity) -> None:
        """Update existing entity (implemented by subclasses).

        Args:
            entity: The entity to update

        Raises:
            EntityNotFoundError: If entity doesn't exist
            ValidationException: If entity validation fails
            TransactionError: If persistence fails

        """
        ...

    @abstractmethod
    async def _delete(self, id: TId) -> None:
        """Hard delete an entity by its ID (implemented by subclasses).

        Note: Hard delete doesn't need to track in seen since entity is removed.

        Args:
            id: The entity's unique identifier

        Raises:
            EntityNotFoundError: If entity doesn't exist
            TransactionError: If deletion fails

        """
        ...

    @abstractmethod
    async def _soft_delete(self, entity: TEntity) -> None:
        """Soft delete an entity (implemented by subclasses).

        Typically marks entity as deleted without removing from database.

        Args:
            entity: The entity to soft delete

        Raises:
            EntityNotFoundError: If entity doesn't exist
            TransactionError: If soft delete fails

        """
        ...

    @abstractmethod
    def stream(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> AsyncIterator[TEntity]:
        """Stream entities for memory-efficient iteration.

        Yields entities one at a time instead of loading all into memory.

        Args:
            skip: Number of entities to skip (for pagination)
            limit: Maximum number of entities to yield (None = unlimited)

        Yields:
            Entities matching the query

        Example:
            async for entity in repository.stream(skip=0, limit=100):
                process(entity)

        """
        ...
