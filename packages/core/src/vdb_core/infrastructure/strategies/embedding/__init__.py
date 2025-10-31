"""Embedding strategy implementations."""

from .cohere_base import BaseCohereStrategy
from .cohere_embed_v3 import (
    BaseCohereEmbeddingStrategy,
    CohereEmbedV3Strategy,
    CohereEnglishLightV3Strategy,
    CohereEnglishV3Strategy,
    CohereMultilingualLightV3Strategy,
    CohereMultilingualV3Strategy,
)
from .cohere_embed_v4 import (
    BaseCohereV4EmbeddingStrategy,
    CohereMultimodalV4Strategy,
)

__all__ = [
    # Base
    "BaseCohereStrategy",
    # Cohere v3
    "BaseCohereEmbeddingStrategy",
    "CohereEmbedV3Strategy",  # Backward compatibility alias
    "CohereEnglishV3Strategy",
    "CohereMultilingualV3Strategy",
    "CohereEnglishLightV3Strategy",
    "CohereMultilingualLightV3Strategy",
    # Cohere v4
    "BaseCohereV4EmbeddingStrategy",
    "CohereMultimodalV4Strategy",
]
