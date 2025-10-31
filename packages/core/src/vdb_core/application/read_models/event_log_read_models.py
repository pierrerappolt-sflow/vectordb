"""Read models for EventLog queries (CQRS pattern)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EventLogReadModel:
    """Read model for EventLog query results.

    Following CQRS:
    - Separate from domain entity
    - Optimized for query performance
    - Contains event metadata and payload
    """

    id: str  # EventLog ID (UUID as string)
    event_type: str  # Type of domain event (e.g., "DocumentCreated", "ChunkEmbedded")
    aggregate_id: str  # ID of the aggregate that produced the event (UUID as string)
    aggregate_type: str  # Type of aggregate (e.g., "Library", "Document", "Chunk")
    payload: dict[str, object]  # Full event payload as JSON
    occurred_at: datetime  # When the event occurred
    created_at: datetime  # When the event was stored
