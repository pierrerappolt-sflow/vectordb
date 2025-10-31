"""Read repository interface for EventLog read operations (CQRS pattern)."""

from abc import ABC, abstractmethod

from vdb_core.application.read_models import EventLogReadModel


class IEventLogReadRepository(ABC):
    """Repository interface for EventLog read operations.

    Following CQRS:
    - Separate from write repository
    - Returns read models (DTOs), not domain entities
    - Optimized for reads with filtering
    - No UoW tracking needed (read-only)
    """

    @abstractmethod
    async def get_by_id(self, event_log_id: str) -> EventLogReadModel | None:
        """Get event log entry by ID.

        Args:
            event_log_id: EventLog ID (UUID string)

        Returns:
            EventLogReadModel if found, None otherwise

        """

    @abstractmethod
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

    @abstractmethod
    async def count(
        self,
        event_type: str | None = None,
        aggregate_type: str | None = None,
    ) -> int:
        """Count total event logs across all libraries.

        Used for pagination to know total result count.

        Args:
            event_type: Optional event type filter
            aggregate_type: Optional aggregate type filter

        Returns:
            Total count of matching events

        """
