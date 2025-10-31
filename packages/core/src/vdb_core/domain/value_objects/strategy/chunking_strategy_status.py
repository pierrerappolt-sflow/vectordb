"""ChunkingStrategyStatus value object - lifecycle status for chunking strategies."""

from enum import StrEnum, auto


class ChunkingStrategyStatus(StrEnum):
    """Enum for chunking strategy status values."""

    ACTIVE = auto()  # "active" - Currently usable in production
    INACTIVE = auto()  # "inactive" - Temporarily disabled
    DEPRECATED = auto()  # "deprecated" - Being phased out, read-only
    BETA = auto()  # "beta" - Testing phase, not production-ready

