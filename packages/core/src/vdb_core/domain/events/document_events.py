"""Document domain events."""

from dataclasses import dataclass

from vdb_core.domain.base import DomainEvent
from vdb_core.domain.value_objects import DocumentFragmentId, DocumentId, DocumentName, LibraryId


@dataclass(frozen=True)
class DocumentCreated(DomainEvent):
    """Event raised when a Document is created."""

    document_id: DocumentId
    library_id: LibraryId
    name: DocumentName


@dataclass(frozen=True)
class DocumentUpdated(DomainEvent):
    """Event raised when a Document is updated."""

    document_id: DocumentId
    library_id: LibraryId
    name: DocumentName


@dataclass(frozen=True)
class DocumentDeleted(DomainEvent):
    """Event raised when a Document is deleted."""

    document_id: DocumentId
    library_id: LibraryId


@dataclass(frozen=True)
class DocumentFragmentReceived(DomainEvent):
    """Event raised when a DocumentFragment is received during streaming upload.

    This event triggers pipeline processing to start as soon as the first fragment arrives,
    enabling streaming processing without waiting for the entire document.
    """

    library_id: LibraryId
    document_id: DocumentId
    fragment_id: DocumentFragmentId
    sequence_number: int
    is_final: bool  # True if this is the last fragment
