"""Tests for InMemoryLibraryRepository."""

from uuid import uuid4

import pytest
from vdb_core.domain.entities import Library
from vdb_core.domain.value_objects import LibraryName
from vdb_core.infrastructure.repositories import InMemoryLibraryRepository


@pytest.mark.asyncio
class TestInMemoryLibraryRepository:
    """Tests for InMemoryLibraryRepository."""

    async def test_add_library(self) -> None:
        """Test adding a library to repository."""
        # Arrange
        repo = InMemoryLibraryRepository()
        library = Library(name=LibraryName(value="Test"))

        # Act
        await repo.add(library)

        # Assert
        assert library in repo.seen

    async def test_get_library_by_id(self) -> None:
        """Test retrieving library by ID."""
        # Arrange
        repo = InMemoryLibraryRepository()
        library = Library(name=LibraryName(value="Test"))
        await repo.add(library)

        # Act
        retrieved = await repo.get(library.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == library.id
        assert retrieved.name.value == "Test"

    async def test_get_nonexistent_library_returns_none(self) -> None:
        """Test getting non-existent library raises EntityNotFoundError."""
        # Arrange
        from vdb_core.domain.exceptions import EntityNotFoundError

        repo = InMemoryLibraryRepository()
        nonexistent_id = uuid4()

        # Act & Assert
        with pytest.raises(EntityNotFoundError, match=f"Entity with id {nonexistent_id} not found"):
            await repo.get(nonexistent_id)

    async def test_update_library(self) -> None:
        """Test updating a library."""
        # Arrange
        repo = InMemoryLibraryRepository()
        library = Library(name=LibraryName(value="Original"))
        await repo.add(library)

        # Act - modify library (using object.__setattr__ since it's frozen)
        object.__setattr__(library, "name", LibraryName(value="Updated"))
        await repo.update(library)

        # Assert
        retrieved = await repo.get(library.id)
        assert retrieved.name.value == "Updated"

    async def test_delete_library(self) -> None:
        """Test deleting a library."""
        # Arrange
        from vdb_core.domain.exceptions import EntityNotFoundError

        repo = InMemoryLibraryRepository()
        library = Library(name=LibraryName(value="Test"))
        await repo.add(library)

        # Act
        await repo.delete(library.id)

        # Assert - getting deleted library should raise error
        with pytest.raises(EntityNotFoundError):
            await repo.get(library.id)

    async def test_stream_libraries(self) -> None:
        """Test streaming all libraries."""
        # Arrange
        repo = InMemoryLibraryRepository()
        library1 = Library(name=LibraryName(value="Test 1"))
        library2 = Library(name=LibraryName(value="Test 2"))
        await repo.add(library1)
        await repo.add(library2)

        # Act
        libraries = [lib async for lib in repo.stream()]

        # Assert
        assert len(libraries) == 2
        library_ids = {lib.id for lib in libraries}
        assert library1.id in library_ids
        assert library2.id in library_ids

    async def test_seen_tracks_aggregates(self) -> None:
        """Test that seen set tracks accessed aggregates."""
        # Arrange
        repo = InMemoryLibraryRepository()
        library = Library(name=LibraryName(value="Test"))

        # Act
        await repo.add(library)

        # Assert
        assert library in repo.seen
        assert len(repo.seen) == 1

    async def test_get_adds_to_seen(self) -> None:
        """Test that get() adds library to seen set."""
        # Arrange
        repo = InMemoryLibraryRepository()
        library = Library(name=LibraryName(value="Test"))
        await repo.add(library)

        # Clear seen
        repo.seen.clear()

        # Act
        retrieved = await repo.get(library.id)

        # Assert
        assert retrieved in repo.seen
