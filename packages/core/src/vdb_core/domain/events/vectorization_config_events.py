"""VectorizationConfig domain events."""

from dataclasses import dataclass

from vdb_core.domain.base import DomainEvent
from vdb_core.domain.value_objects import (
    DocumentId,
    LibraryId,
    VectorizationConfigId,
)


@dataclass(frozen=True)
class DocumentVectorizationPending(DomainEvent):
    """Event raised when a document needs vectorization processing with a config."""

    document_id: DocumentId
    config_id: VectorizationConfigId
    library_id: LibraryId


@dataclass(frozen=True)
class DocumentVectorizationCompleted(DomainEvent):
    """Event raised when document processing with a config completes successfully."""

    document_id: DocumentId
    config_id: VectorizationConfigId
    library_id: LibraryId


@dataclass(frozen=True)
class DocumentVectorizationFailed(DomainEvent):
    """Event raised when document processing with a config fails."""

    document_id: DocumentId
    config_id: VectorizationConfigId
    library_id: LibraryId
    error_message: str
