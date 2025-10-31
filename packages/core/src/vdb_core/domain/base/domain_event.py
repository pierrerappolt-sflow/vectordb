"""Base domain event class."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Events are immutable records of things that have happened in the domain.
    They are raised by aggregates when their state changes.
    """

    event_id: str = field(init=False)
    occurred_at: datetime = field(init=False)

    def __post_init__(self) -> None:
        """Initialize event metadata."""
        # Use object.__setattr__ because dataclass is frozen
        object.__setattr__(self, "event_id", str(uuid4()))
        object.__setattr__(self, "occurred_at", datetime.now(UTC))
