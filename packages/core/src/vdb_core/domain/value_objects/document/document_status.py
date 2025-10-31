"""DocumentStatus value object - status of a Document entity."""

from enum import StrEnum, auto
from typing import final


@final
class DocumentStatus(StrEnum):
    """Enum for document status values."""

    PENDING = auto()  # Document created, awaiting processing
    PROCESSING = auto()  # Document being chunked
    COMPLETED = auto()  # Document chunked and ready
    FAILED = auto()  # Document processing failed
    DELETED = auto()  # Document marked for deletion

