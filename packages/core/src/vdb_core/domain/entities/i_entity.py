"""Base entity interface for domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from vdb_core.utils import utc_now


@dataclass(slots=True, kw_only=True, eq=False)
class IEntity:
    """Base class for domain entities."""

    id: UUID = field(default_factory=uuid4, init=False)
    created_at: datetime = field(default_factory=utc_now, init=False)
    updated_at: datetime = field(default_factory=utc_now, init=False)

    def __hash__(self) -> int:
        """Hash entities by their id."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Compare entities by their id and type."""
        return isinstance(other, IEntity) and type(self) is type(other) and self.id == other.id
