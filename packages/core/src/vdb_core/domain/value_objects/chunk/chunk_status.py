"""ChunkStatus value object - status of a Chunk entity."""

from enum import StrEnum, auto
from typing import final


@final
class ChunkStatus(StrEnum):
    """Enum for chunk status values."""

    PENDING = auto()  # Chunk created, awaiting processing
    PROCESSING = auto()  # Chunk is being processed
    COMPLETED = auto()  # Chunk fully processed
    FAILED = auto()  # Chunk processing failed
    DELETED = auto()  # Chunk marked for deletion

