"""VectorizationConfig domain events."""

from dataclasses import dataclass

from vdb_core.domain.base import DomainEvent
from vdb_core.domain.value_objects import (
    ConfigStatus,
    DocumentId,
    LibraryId,
    VectorizationConfigId,
)


@dataclass(frozen=True)
class VectorizationConfigCreated(DomainEvent):
    """Event raised when a VectorizationConfig is created.

    This event is raised when a new version 1 config is created
    (typically during bootstrap or by admin).
    """

    config_id: VectorizationConfigId
    version: int
    status: ConfigStatus
    description: str | None = None


@dataclass(frozen=True)
class VectorizationConfigVersionCreated(DomainEvent):
    """Event raised when a new version of a VectorizationConfig is created.

    This event is raised when editing a config creates a new version.
    The old version should be marked as deprecated.

    This event should trigger auto-upgrade of all libraries using the
    previous version to the new version.
    """

    config_id: VectorizationConfigId
    version: int
    previous_version_id: VectorizationConfigId
    status: ConfigStatus
    description: str | None = None


@dataclass(frozen=True)
class VectorizationConfigUpdated(DomainEvent):
    """Event raised when a VectorizationConfig's properties are modified.

    This event is raised when chunking/embedding strategies, parameters,
    or other config properties are changed. This should trigger re-processing
    of all documents in all libraries using this config.

    Note: This is different from VectorizationConfigVersionCreated, which
    creates a new version. This event is for in-place updates.
    """

    config_id: VectorizationConfigId
    affected_library_ids: list[LibraryId]
    changes_description: str | None = None


@dataclass(frozen=True)
class LibraryConfigAdded(DomainEvent):
    """Event raised when a VectorizationConfig is added to a Library.

    This event should trigger processing of all existing documents
    in the library with the new config.
    """

    library_id: LibraryId
    config_id: VectorizationConfigId


@dataclass(frozen=True)
class LibraryConfigRemoved(DomainEvent):
    """Event raised when a VectorizationConfig is removed from a Library.

    Note: This does NOT delete the config itself (configs are global).
    It only removes the association between library and config.
    """

    library_id: LibraryId
    config_id: VectorizationConfigId


@dataclass(frozen=True)
class DocumentVectorizationPending(DomainEvent):
    """Event raised when a document needs vectorization processing with a config.

    This event is raised when:
    - A new config is added to a library (process all existing documents)
    - A new document is uploaded (process with all library configs)
    - A config version is upgraded (reprocess all documents)
    """

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
