"""In-memory message bus implementation for testing and development."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.message_bus import IMessageBus

if TYPE_CHECKING:
    from vdb_core.domain.events import DomainEvent


class InMemoryMessageBus(IMessageBus):
    """In-memory implementation of message bus.

    Stores handled events in memory for inspection/testing.
    Does not route to handlers yet (can be extended).

    Following Cosmic Python pattern (Chapter 9):
    - Message bus receives events after UoW commit
    - Routes events to registered handlers
    - For now: just stores for inspection

    Useful for:
    - Testing: Verify which events were handled
    - Development: See event flow without handlers
    - Debugging: Inspect event sequences

    Example:
        message_bus = InMemoryMessageBus()
        await message_bus.handle_events([LibraryCreated(...)])

        # Inspect handled events
        assert len(message_bus.handled_events) == 1
        assert isinstance(message_bus.handled_events[0], LibraryCreated)

    """

    def __init__(self) -> None:
        """Initialize empty message bus."""
        self.handled_events: list[DomainEvent] = []

    async def handle_events(self, events: list[DomainEvent]) -> None:
        """Handle a batch of domain events.

        For now, just stores events. In full implementation:
        - Route to registered handlers based on event type
        - Execute handlers in order
        - Handle failures/retries

        Args:
            events: List of domain events to handle

        """
        for event in events:
            self.handled_events.append(event)

    def clear(self) -> None:
        """Clear all handled events (useful for tests)."""
        self.handled_events.clear()

    def get_events_of_type(self, event_type: type[DomainEvent]) -> list[DomainEvent]:
        """Get all handled events of a specific type.

        Args:
            event_type: The event class to filter by

        Returns:
            List of events matching the type

        """
        return [event for event in self.handled_events if isinstance(event, event_type)]

    def __len__(self) -> int:
        """Get count of handled events."""
        return len(self.handled_events)
