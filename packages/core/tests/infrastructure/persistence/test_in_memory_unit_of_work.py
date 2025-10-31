"""Tests for InMemoryUnitOfWork."""

import pytest
from vdb_core.domain.entities import Library
from vdb_core.domain.events import LibraryCreated
from vdb_core.domain.value_objects import LibraryName
from vdb_core.infrastructure.persistence import InMemoryUnitOfWork


@pytest.mark.asyncio
class TestInMemoryUnitOfWork:
    """Tests for InMemoryUnitOfWork."""

    async def test_uow_context_manager(self) -> None:
        """Test UoW works as async context manager."""
        # Arrange
        uow = InMemoryUnitOfWork()

        # Act & Assert
        async with uow:
            assert uow.libraries is not None

    async def test_uow_commit_collects_events(self) -> None:
        """Test that commit collects events from aggregates."""
        # Arrange
        uow = InMemoryUnitOfWork()
        library = Library(name=LibraryName(value="Test"))

        # Act
        async with uow:
            await uow.libraries.add(library)
            events = await uow.commit()

        # Assert
        assert len(events) == 1
        assert isinstance(events[0], LibraryCreated)
        assert events[0].library_id == library.id

    async def test_uow_commit_clears_events_after_collection(self) -> None:
        """Test that events are cleared after commit."""
        # Arrange
        uow = InMemoryUnitOfWork()
        library = Library(name=LibraryName(value="Test"))

        # Act
        async with uow:
            await uow.libraries.add(library)
            events1 = await uow.commit()

        async with uow:
            # Second commit should have no events
            events2 = await uow.commit()

        # Assert
        assert len(events1) == 1
        assert len(events2) == 0

    async def test_uow_multiple_aggregates_collect_all_events(self) -> None:
        """Test that events from multiple aggregates are all collected."""
        # Arrange
        uow = InMemoryUnitOfWork()
        library1 = Library(name=LibraryName(value="Test 1"))
        library2 = Library(name=LibraryName(value="Test 2"))

        # Act
        async with uow:
            await uow.libraries.add(library1)
            await uow.libraries.add(library2)
            events = await uow.commit()

        # Assert
        assert len(events) == 2
        library_ids = {e.library_id for e in events}  # type: ignore[attr-defined]
        assert library1.id in library_ids
        assert library2.id in library_ids
