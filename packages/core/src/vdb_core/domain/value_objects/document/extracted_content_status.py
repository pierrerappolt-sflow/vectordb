"""ExtractedContentStatus - status for extracted content entities."""

from enum import StrEnum, auto

class ExtractedContentStatus(StrEnum):
    """Extracted content lifecycle states.

    PENDING: Created, waiting to be chunked
    CHUNKED: Successfully chunked by at least one VectorizationJob
    FAILED: Chunking failed
    """

    PENDING = auto()
    CHUNKED = auto()
    FAILED = auto()

