"""Message bus interface for routing commands and events to handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vdb_core.domain.events import DomainEvent


class IMessageBus(ABC):
    """Internal message bus for routing commands and events to handlers.

    Following Cosmic Python pattern (Chapter 9-10):
    - Receives commands and events
    - Routes them to appropriate handlers
    - Handlers perform the actual work
    - Supports handler registration

    Difference from EventBus/EventPublisher:
    - IMessageBus: Internal routing within service layer
    - EventPublisher: External publishing to message broker (Kafka, RabbitMQ, etc.)

    Usage:
        # In use case
        async with uow:
            library = Library(name=LibraryName("Test"))
            await uow.libraries.add(library)

            events = await uow.commit()

        # Route events to handlers
        await message_bus.handle_events(events)

    Example handler:
        @message_bus.register_handler(LibraryCreated)
        async def on_library_created(event: LibraryCreated):
            # Start processing workflow
            await temporal_client.start_workflow(...)
    """

    @abstractmethod
    async def handle_events(self, events: list[DomainEvent]) -> None:
        """Handle a batch of domain events.

        Routes each event to all registered handlers for that event type.
        Handlers are called in registration order.

        Args:
            events: List of domain events to handle

        Note:
            Events should only be handled AFTER successful transaction commit.
            This ensures handlers never process events for rolled-back operations.

        """
