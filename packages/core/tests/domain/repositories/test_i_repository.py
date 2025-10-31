"""Tests for generic repository interface."""

from collections.abc import AsyncIterator

import pytest
from vdb_core.domain.base import AbstractRepository
from vdb_core.domain.entities import Library
from vdb_core.domain.value_objects import LibraryId


class MockLibraryRepository(AbstractRepository[Library, LibraryId]):
    """Mock implementation for testing.

    Follows Cosmic Python pattern - inherits seen tracking from AbstractRepository.
    Only implements private methods (_add, _get, _update, _delete).
    """

    def __init__(self) -> None:
        """Initialize with empty storage."""
        super().__init__()  # Get self.seen from AbstractRepository
        self._storage: dict[str, Library] = {}

    async def _add(self, entity: Library) -> None:
        """Add entity to mock storage."""
        self._storage[str(entity.id)] = entity

    async def _get(self, id: LibraryId) -> Library | None:
        """Get entity from mock storage."""
        return self._storage.get(str(id))

    async def _update(self, entity: Library) -> None:
        """Update entity in mock storage."""
        self._storage[str(entity.id)] = entity

    async def _delete(self, id: LibraryId) -> None:
        """Delete entity from mock storage."""
        self._storage.pop(str(id), None)

    async def _soft_delete(self, entity: Library) -> None:
        """Soft delete entity (mark as deleted)."""
        # For mock, just update the status to DELETED
        from vdb_core.domain.value_objects import LibraryStatus

        entity.update(status=LibraryStatus.DELETED)
        await self._update(entity)

    async def stream(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> AsyncIterator[Library]:
        """Stream entities from mock storage."""
        entities = list(self._storage.values())
        end = len(entities) if limit is None else skip + limit

        for entity in entities[skip:end]:
            yield entity


@pytest.mark.asyncio
async def test_repository_add_and_get() -> None:
    """Test that repository can add and retrieve entities."""
    from vdb_core.domain.value_objects import LibraryName

    repo = MockLibraryRepository()
    library = Library(name=LibraryName(value="Test Library"))

    await repo.add(library)
    retrieved = await repo.get(library.id)

    assert retrieved is not None
    assert retrieved.id == library.id
    assert retrieved.name == library.name


@pytest.mark.asyncio
async def test_repository_update() -> None:
    """Test that repository can update entities."""
    from vdb_core.domain.value_objects import LibraryName

    repo = MockLibraryRepository()
    library = Library(name=LibraryName(value="Test Library"))

    await repo.add(library)

    # Update entity
    updated_library = Library(name=LibraryName(value="Updated Library"))
    object.__setattr__(updated_library, "id", library.id)
    await repo.update(updated_library)

    retrieved = await repo.get(library.id)
    assert retrieved is not None
    assert retrieved.name.value == "Updated Library"


@pytest.mark.asyncio
async def test_repository_delete() -> None:
    """Test that repository can delete entities."""
    from vdb_core.domain.exceptions import EntityNotFoundError
    from vdb_core.domain.value_objects import LibraryName

    repo = MockLibraryRepository()
    library = Library(name=LibraryName(value="Test Library"))

    await repo.add(library)
    await repo.delete(library.id)

    # Deleted entity should raise EntityNotFoundError
    with pytest.raises(EntityNotFoundError):
        await repo.get(library.id)


@pytest.mark.asyncio
async def test_repository_stream() -> None:
    """Test that repository can stream entities."""
    from vdb_core.domain.value_objects import LibraryName

    repo = MockLibraryRepository()

    # Add multiple entities
    libraries = [Library(name=LibraryName(value=f"Library {i}")) for i in range(5)]
    for library in libraries:
        await repo.add(library)

    # Stream all entities
    streamed = [library async for library in repo.stream()]

    assert len(streamed) == 5


@pytest.mark.asyncio
async def test_repository_stream_with_pagination() -> None:
    """Test that repository streaming supports pagination."""
    from vdb_core.domain.value_objects import LibraryName

    repo = MockLibraryRepository()

    # Add multiple entities
    libraries = [Library(name=LibraryName(value=f"Library {i}")) for i in range(10)]
    for library in libraries:
        await repo.add(library)

    # Stream with skip and limit
    streamed = [library async for library in repo.stream(skip=2, limit=3)]

    assert len(streamed) == 3
