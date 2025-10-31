"""EventLog model - infrastructure persistence model for event logging.

This is NOT a domain entity - it's an infrastructure concern for observability.
Pure data structure with no business logic.
Used for type safety and representing event_logs table.

Moved from domain layer as event logging is an infrastructure/observability concern,
not core business logic.
"""

from dataclasses import dataclass
from datetime import datetime

from .event_log_id import EventLogId


@dataclass(slots=True, kw_only=True)
class EventLog:
    """Event log entry - captures all pipeline events.

    This is a pure data model, not business logic.
    Used for monitoring, debugging, and auditing.

    Attributes:
        id: Unique identifier (UUID)
        event_type: Event class name (e.g., "FragmentDecoded")
        event_id: Original event ID from domain event
        timestamp: When event occurred
        routing_key: RabbitMQ routing key
        data: Event payload as dict
        document_id: Extracted document ID (for indexing)
        library_id: Extracted library ID (for indexing)
        pipeline_stage: Inferred stage (upload, decode, chunk, embed, index)

    """

    id: EventLogId
    event_type: str
    timestamp: datetime
    routing_key: str
    data: dict[str, object]
    event_id: str | None = None
    document_id: str | None = None
    library_id: str | None = None
    pipeline_stage: str | None = None

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.event_type:
            msg = "event_type is required"
            raise ValueError(msg)
        if not self.routing_key:
            msg = "routing_key is required"
            raise ValueError(msg)
