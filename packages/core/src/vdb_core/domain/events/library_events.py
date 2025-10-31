"""Library domain events."""

from dataclasses import dataclass

from vdb_core.domain.base import DomainEvent
from vdb_core.domain.value_objects import LibraryId, LibraryName, VectorizationConfigId


@dataclass(frozen=True)
class LibraryCreated(DomainEvent):
    """Event raised when a Library is created."""

    library_id: LibraryId
    name: LibraryName


@dataclass(frozen=True)
class LibraryUpdated(DomainEvent):
    """Event raised when a Library is updated."""

    library_id: LibraryId
    name: LibraryName


@dataclass(frozen=True)
class LibraryDeleted(DomainEvent):
    """Event raised when a Library is deleted."""

    library_id: LibraryId


@dataclass(frozen=True)
class LibraryConfigAdded(DomainEvent):
    """Event raised when a VectorizationConfig is associated with a Library."""

    library_id: LibraryId
    config_id: VectorizationConfigId


@dataclass(frozen=True)
class LibraryConfigRemoved(DomainEvent):
    """Event raised when a VectorizationConfig is disassociated from a Library."""

    library_id: LibraryId
    config_id: VectorizationConfigId
