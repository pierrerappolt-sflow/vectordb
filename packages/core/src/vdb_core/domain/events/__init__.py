"""Domain events exports."""

from vdb_core.domain.base import DomainEvent

from .document_events import (
    DocumentCreated,
    DocumentDeleted,
    DocumentFragmentReceived,
    DocumentUpdated,
)
from .library_events import LibraryCreated
from .extracted_content_events import ExtractedContentCreated
from .vectorization_config_events import (
    DocumentVectorizationCompleted,
    DocumentVectorizationFailed,
    DocumentVectorizationPending,
)

__all__ = [
    # Base
    "DomainEvent",
    # Document events
    "DocumentCreated",
    "DocumentDeleted",
    "DocumentFragmentReceived",
    "DocumentUpdated",
    # Vectorization config events
    "DocumentVectorizationCompleted",
    "DocumentVectorizationFailed",
    "DocumentVectorizationPending",
    # Library
    "LibraryCreated",
    # Extracted content
    "ExtractedContentCreated",
]
