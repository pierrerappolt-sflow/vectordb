"""EventLog queries for read operations (CQRS pattern)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetEventLogsQuery:
    """Query to get all event logs across all libraries.

    Following CQRS:
    - Queries are immutable
    - Contains only filter/pagination params
    - No business logic

    Attributes:
        event_type: Optional event type filter (e.g., "DocumentCreated")
        aggregate_type: Optional aggregate type filter (e.g., "Document", "Chunk")
        limit: Maximum number of events to return
        offset: Number of events to skip for pagination

    """

    event_type: str | None = None
    aggregate_type: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetEventLogByIdQuery:
    """Query to get a specific event log by ID.

    Attributes:
        event_log_id: The event log's unique identifier (UUID string)

    """

    event_log_id: str
