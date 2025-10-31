"""In-memory implementation of EventLog read repository (CQRS read side)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.repositories import IEventLogReadRepository

if TYPE_CHECKING:
    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.read_models import EventLogReadModel


class InMemoryEventLogReadRepository(IEventLogReadRepository):
    """In-memory implementation of EventLog read repository.

    Following CQRS:
    - Read-only operations
    - Returns read models (DTOs), not domain entities
    - No UoW tracking (queries don't modify state)

    Implementation approach:
    - Accesses event logs from the message bus's handled_events
    - Converts domain events to read models on the fly
    - Supports filtering by library_id, event_type, and aggregate_type
    """

    def __init__(self, unit_of_work: IUnitOfWork) -> None:
        """Initialize read repository.

        Args:
            unit_of_work: Unit of work for accessing message bus (via container)

        Note:
            In production, this would query from a dedicated event store or database.
            For now, we'll create our own storage since UoW doesn't have event log access.

        """
        # For in-memory implementation, we'll maintain our own event log store
        # In production, this would query from a persistent event store
        self._event_logs: list[EventLogReadModel] = []

    def _add_event_log(self, event_log: EventLogReadModel) -> None:
        """Add an event log to storage (internal method for testing/development).

        Args:
            event_log: Event log read model to store

        """
        self._event_logs.append(event_log)

    async def get_all(
        self,
        event_type: str | None = None,
        aggregate_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventLogReadModel]:
        """Get all event logs across all libraries.

        Args:
            event_type: Optional event type filter (e.g., "DocumentCreated")
            aggregate_type: Optional aggregate type filter (e.g., "Document")
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of EventLogReadModel instances ordered by occurred_at descending

        """
        # Start with all events
        filtered_events = list(self._event_logs)

        # Apply event_type filter if provided
        if event_type:
            filtered_events = [event for event in filtered_events if event.event_type == event_type]

        # Apply aggregate_type filter if provided
        if aggregate_type:
            filtered_events = [event for event in filtered_events if event.aggregate_type == aggregate_type]

        # Sort by occurred_at descending (most recent first)
        filtered_events.sort(key=lambda e: e.occurred_at, reverse=True)

        # Apply pagination
        return filtered_events[offset : offset + limit]

    async def get_by_id(self, event_log_id: str) -> EventLogReadModel | None:
        """Get event log by ID.

        Args:
            event_log_id: Event log ID (UUID string)

        Returns:
            EventLogReadModel if found, None otherwise

        """
        for event_log in self._event_logs:
            if event_log.id == event_log_id:
                return event_log
        return None

    async def count(
        self,
        event_type: str | None = None,
        aggregate_type: str | None = None,
    ) -> int:
        """Count event logs across all libraries.

        Args:
            event_type: Optional event type filter
            aggregate_type: Optional aggregate type filter

        Returns:
            Total count of matching events

        """
        # Start with all events
        filtered_events = list(self._event_logs)

        # Apply event_type filter if provided
        if event_type:
            filtered_events = [event for event in filtered_events if event.event_type == event_type]

        # Apply aggregate_type filter if provided
        if aggregate_type:
            filtered_events = [event for event in filtered_events if event.aggregate_type == aggregate_type]

        return len(filtered_events)

    def _extract_library_id(self, payload: dict[str, object]) -> str | None:
        """Extract library_id from event payload.

        Args:
            payload: Event payload dictionary

        Returns:
            Library ID if found, None otherwise

        """
        # Try to get library_id from payload
        library_id = payload.get("library_id")
        if library_id:
            return str(library_id)

        # Some events might have nested library_id
        # Add more extraction logic as needed
        return None
