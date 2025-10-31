"""Base entity interface for domain entities."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from vdb_core.utils import utc_now

if TYPE_CHECKING:
    from datetime import datetime

    from vdb_core.domain.events import DomainEvent


@dataclass(kw_only=True, eq=False)
class IEntity(ABC):
    """Base class for domain entities with event support.

    Following Cosmic Python pattern:
    - Entities have an `events` list
    - Events are appended directly: `self.events.append(event)`
    - UoW collects events from aggregates in `self.libraries.seen`

    All entities:
    - Have a unique ID (defined by subclasses)
    - Track created_at and updated_at timestamps
    - Are compared by ID and type
    - Can be hashed by ID

    DDD invariant protection:
    - Direct field assignment is blocked after initialization
    - All mutations must go through update() method or specific entity methods
    - Subclasses define which fields are mutable via _mutable_fields
    """

    id: Any  # Will be overridden by subclasses with specific ID types
    created_at: datetime = field(default_factory=utc_now, init=False)
    updated_at: datetime = field(default_factory=utc_now, init=False)
    events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)
    _allow_setattr: bool = field(default=True, init=False, repr=False)

    # Subclasses should override this to define which fields can be updated
    _mutable_fields: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Mark entity initialization as complete."""
        object.__setattr__(self, "_allow_setattr", False)

    def __setattr__(self, name: str, value: Any) -> None:
        """Block all direct field assignments after initialization.

        This enforces DDD principle: all mutations must go through entity methods.

        Raises:
            AttributeError: If attempting to set field after initialization

        """
        # Allow assignment during __init__ and __post_init__
        if not hasattr(self, "_allow_setattr") or object.__getattribute__(self, "_allow_setattr"):
            object.__setattr__(self, name, value)
            return

        msg = (
            f"Cannot directly assign to '{name}' on {type(self).__name__}. "
            f"Use update() method or specific entity methods instead."
        )
        raise AttributeError(msg)

    def update(self, **kwargs: Any) -> None:
        """Update mutable fields on this entity.

        Args:
            **kwargs: Field names and values to update

        Raises:
            AttributeError: If trying to update an immutable field

        Example:
            library.update(name=LibraryName(value="New Name"))

        """
        for field_name, value in kwargs.items():
            if field_name not in self._mutable_fields:
                msg = (
                    f"Cannot update field '{field_name}' on {type(self).__name__}. "
                    f"Mutable fields: {sorted(self._mutable_fields)}"
                )
                raise AttributeError(msg)

            object.__setattr__(self, field_name, value)

        # Auto-update timestamp
        object.__setattr__(self, "updated_at", utc_now())

    def __hash__(self) -> int:
        """Hash entities by their id."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Compare entities by their id and type."""
        return isinstance(other, IEntity) and type(self) is type(other) and self.id == other.id

    def collect_all_events(self) -> list[DomainEvent]:
        """Collect all events from this entity and clear the event list.

        For aggregate roots, override this to also collect events from child entities.
        For simple entities, this base implementation collects only direct events.

        Returns:
            List of all domain events from this entity

        """
        events = self.events.copy()
        self.events.clear()
        return events
