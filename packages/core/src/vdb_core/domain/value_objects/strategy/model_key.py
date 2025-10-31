"""Model keys for strategies."""

from enum import StrEnum


class ChunkingModelKey(StrEnum):
    """Chunking strategy identifiers.

    Values must match registrations in `strategy_resolver`:
    - "cohere-token-256"
    - "cohere-token-1024"
    """

    COHERE_TOKEN_256 = "cohere-token-256"
    COHERE_TOKEN_1024 = "cohere-token-1024"


class EmbedModelKey(StrEnum):
    """Legacy combined keys (kept for backward compatibility)."""

    TOKEN_256 = "token-256"
    TOKEN_1024 = "token-1024"

    EMBED_ENGLISH_V3 = "embed-english-v3.0"
    EMBED_ENGLISH_LIGHT_V3 = "embed-english-light-v3.0"
    EMBED_MULTILINGUAL_V3 = "embed-multilingual-v3.0"
    EMBED_MULTILINGUAL_LIGHT_V3 = "embed-multilingual-light-v3.0"
    EMBED_MULTIMODAL_V4 = "embed-multimodal-v4.0"
