"""EmbeddingStrategyStatus value object - lifecycle status for embedding strategies."""

from enum import StrEnum, auto




class EmbeddingStrategyStatus(StrEnum):
    """Enum for embedding strategy status values."""

    ACTIVE = auto()  # "active" - Currently usable in production
    INACTIVE = auto()  # "inactive" - Temporarily disabled
    DEPRECATED = auto()  # "deprecated" - Being phased out, read-only
    BETA = auto()  # "beta" - Testing phase, not production-ready



def default_embedding_strategy_status() -> EmbeddingStrategyStatus:
    """Factory for default embedding strategy status.

    Returns:
        EmbeddingStrategyStatus with BETA value (new strategies start in beta)

    """
    return EmbeddingStrategyStatus.BETA
