"""ChunkingBehavior - defines how content is processed into chunks."""

from enum import StrEnum, auto
from typing import final


@final
class ChunkingBehavior(StrEnum):
    """Defines how content is processed into chunks.

    Different modalities require different chunking approaches:
    - SPLIT: Split content into multiple overlapping pieces (TEXT)
    - PASSTHROUGH: Single chunk containing entire content (IMAGE, full VIDEO)
    - FRAME_EXTRACT: Extract frames as individual chunks (VIDEO)
    - TIME_SEGMENT: Split into time-based segments (AUDIO)
    """

    SPLIT = auto()
    PASSTHROUGH = auto()
    FRAME_EXTRACT = auto()
    TIME_SEGMENT = auto()
