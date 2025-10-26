"""Document entity - aggregate containing chunks."""

from dataclasses import dataclass
from uuid import UUID

from .i_entity import IEntity


@dataclass(slots=True, kw_only=True, eq=False)
class Document(IEntity):
    """Document aggregate containing text chunks."""

    library_id: UUID
    name: str
