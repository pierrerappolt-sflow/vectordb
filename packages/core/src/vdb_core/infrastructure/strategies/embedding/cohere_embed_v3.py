"""Cohere embedding strategy implementations for v3 models."""

from __future__ import annotations

from functools import lru_cache

from vdb_core.domain.value_objects import ModalityType
from vdb_core.domain.value_objects.strategy.model_key import EmbedModelKey

from .cohere_base import BaseCohereStrategy


class BaseCohereEmbeddingStrategy(BaseCohereStrategy):
    """Base class for all Cohere v3 embedding strategies.

    Inherits common Cohere logic from BaseCohereStrategy:
    - API client initialization
    - Rate limiting and retry logic
    - Error handling

    Subclasses define:
    - Model name
    - Dimensions
    - Identifier
    """

    @property
    def supported_modalities(self) -> frozenset[ModalityType]:
        """Return supported modalities (TEXT only for all v3 models)."""
        return frozenset([ModalityType.TEXT])

    def supports_modality(self, modality: ModalityType) -> bool:
        """Check if this strategy supports the given modality."""
        return modality in self.supported_modalities

    @lru_cache(maxsize=1000)
    async def _embed_cached(
        self,
        texts: tuple[str, ...],
        input_type: str,
    ) -> tuple[tuple[float, ...], ...]:
        """Cached embed implementation (hashable arguments).

        Args:
            texts: Tuple of text strings
            input_type: Input type for Cohere API ("search_query" or "search_document")

        Returns:
            Tuple of embedding tuples

        """
        # Call Cohere API with retry logic
        embeddings = await self._call_cohere_with_retry(list(texts), input_type=input_type)
        # Convert to tuple of tuples for caching
        return tuple(tuple(emb) for emb in embeddings)

    async def embed(
        self,
        content: list[str | bytes],
        input_type: str = "search_document",
    ) -> list[list[float]]:
        """Generate embedding vectors from batch of text content.

        Args:
            content: List of text content to embed (must be str for TEXT modality)
            input_type: Purpose of embedding ("search_query" or "search_document")

        Returns:
            List of dense embedding vectors

        Raises:
            TypeError: If content items are not strings
            ValueError: If any content is empty or API returns wrong dimensions

        """
        # Validate all content items are strings
        texts = []
        for item in content:
            if not isinstance(item, str):
                msg = f"Content must be str for TEXT modality, got {type(item)}"
                raise TypeError(msg)

            if not item or not item.strip():
                msg = "Content cannot be empty"
                raise ValueError(msg)

            texts.append(item)

        # Call cached version with tuple
        cached_result = await self._embed_cached(tuple(texts), input_type)
        # Convert back to list of lists
        return [list(emb) for emb in cached_result]


class CohereEnglishV3Strategy(BaseCohereEmbeddingStrategy):
    """Cohere embed-english-v3.0 - English text embeddings (1024 dimensions)."""

    @property
    def identifier(self) -> str:
        """Return the strategy identifier."""
        return EmbedModelKey.EMBED_ENGLISH_V3.value

    @property
    def model_name(self) -> str:
        """Return the Cohere model name."""
        return "embed-english-v3.0"

    @property
    def dimensions(self) -> int:
        """Return vector dimensions (1024 for standard v3)."""
        return 1024


class CohereMultilingualV3Strategy(BaseCohereEmbeddingStrategy):
    """Cohere embed-multilingual-v3.0 - Multilingual text embeddings (1024 dimensions)."""

    @property
    def identifier(self) -> str:
        """Return the strategy identifier."""
        return EmbedModelKey.EMBED_MULTILINGUAL_V3.value

    @property
    def model_name(self) -> str:
        """Return the Cohere model name."""
        return "embed-multilingual-v3.0"

    @property
    def dimensions(self) -> int:
        """Return vector dimensions (1024 for standard v3)."""
        return 1024


class CohereEnglishLightV3Strategy(BaseCohereEmbeddingStrategy):
    """Cohere embed-english-light-v3.0 - English text embeddings (384 dimensions, faster)."""

    @property
    def identifier(self) -> str:
        """Return the strategy identifier."""
        return EmbedModelKey.EMBED_ENGLISH_LIGHT_V3.value

    @property
    def model_name(self) -> str:
        """Return the Cohere model name."""
        return "embed-english-light-v3.0"

    @property
    def dimensions(self) -> int:
        """Return vector dimensions (384 for light v3)."""
        return 384


class CohereMultilingualLightV3Strategy(BaseCohereEmbeddingStrategy):
    """Cohere embed-multilingual-light-v3.0 - Multilingual text embeddings (384 dimensions, faster)."""

    @property
    def identifier(self) -> str:
        """Return the strategy identifier."""
        return EmbedModelKey.EMBED_MULTILINGUAL_LIGHT_V3.value

    @property
    def model_name(self) -> str:
        """Return the Cohere model name."""
        return "embed-multilingual-light-v3.0"

    @property
    def dimensions(self) -> int:
        """Return vector dimensions (384 for light v3)."""
        return 384


# Backward compatibility alias
CohereEmbedV3Strategy = CohereEnglishV3Strategy
