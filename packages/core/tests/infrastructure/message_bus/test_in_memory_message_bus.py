"""Tests for InMemoryMessageBus."""

from uuid import uuid4

import pytest
from vdb_core.domain.events import DocumentCreated, LibraryCreated
from vdb_core.infrastructure.message_bus import InMemoryMessageBus


@pytest.mark.asyncio
class TestInMemoryMessageBus:
    """Tests for InMemoryMessageBus."""

    async def test_handle_events_stores_events(self) -> None:
        """Test that handle_events stores all events."""
        # Arrange
        bus = InMemoryMessageBus()
        from vdb_core.domain.value_objects import DocumentName, LibraryName

        events = [
            LibraryCreated(library_id=uuid4(), name=LibraryName(value="Test")),
            DocumentCreated(
                document_id=uuid4(),
                library_id=uuid4(),
                name=DocumentName("Test"),
            ),
        ]

        # Act
        await bus.handle_events(events)

        # Assert
        assert len(bus.handled_events) == 2
        assert isinstance(bus.handled_events[0], LibraryCreated)
        assert isinstance(bus.handled_events[1], DocumentCreated)

    async def test_handle_events_with_empty_list(self) -> None:
        """Test handling empty event list."""
        # Arrange
        bus = InMemoryMessageBus()

        # Act
        await bus.handle_events([])

        # Assert
        assert len(bus.handled_events) == 0

    async def test_handle_events_multiple_times(self) -> None:
        """Test that events accumulate across multiple calls."""
        # Arrange
        bus = InMemoryMessageBus()
        from vdb_core.domain.value_objects import LibraryName

        # Act
        await bus.handle_events([LibraryCreated(library_id=uuid4(), name=LibraryName(value="Test 1"))])
        await bus.handle_events([LibraryCreated(library_id=uuid4(), name=LibraryName(value="Test 2"))])

        # Assert
        assert len(bus.handled_events) == 2
