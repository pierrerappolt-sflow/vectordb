"""Cohere embedding strategy implementations for v4 models (multimodal)."""

from __future__ import annotations

from functools import lru_cache

from vdb_core.domain.value_objects import ModalityType

from .cohere_base import BaseCohereStrategy


class BaseCohereV4EmbeddingStrategy(BaseCohereStrategy):
    """Base class for Cohere v4 embedding strategies (multimodal support).

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
        """Return supported modalities (TEXT and IMAGE for v4 multimodal)."""
        return frozenset([ModalityType.TEXT, ModalityType.IMAGE])

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
            texts: Tuple of text/base64 strings
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
        """Generate embedding vectors from batch of content.

        Args:
            content: List of text or image content to embed
                - str: Text content
                - bytes: Image content (will be base64 encoded)
            input_type: Purpose of embedding ("search_query" or "search_document")

        Returns:
            List of dense embedding vectors

        Raises:
            TypeError: If content type is not supported
            ValueError: If any content is empty or API returns wrong dimensions

        """
        # Prepare content for API
        texts = []
        for item in content:
            if isinstance(item, str):
                if not item or not item.strip():
                    msg = "Content cannot be empty"
                    raise ValueError(msg)
                texts.append(item)
            elif isinstance(item, bytes):
                # For images, Cohere expects base64 encoded strings
                import base64
                encoded = base64.b64encode(item).decode("utf-8")
                texts.append(encoded)
            else:
                msg = f"Unsupported content type: {type(item)}"
                raise TypeError(msg)

        # Call cached version with tuple
        cached_result = await self._embed_cached(tuple(texts), input_type)
        # Convert back to list of lists
        return [list(emb) for emb in cached_result]


class CohereMultimodalV4Strategy(BaseCohereV4EmbeddingStrategy):
    """Cohere embed-multimodal-v4.0 - Multimodal embeddings (1024 dimensions).

    NOTE: Currently returns stub zero vectors as the model is not yet available.
    """

    @property
    def identifier(self) -> str:
        """Return the strategy identifier."""
        return "cohere/embed-multimodal-v4.0"

    @property
    def model_name(self) -> str:
        """Return the Cohere model name."""
        return "embed-multimodal-v4.0"

    @property
    def dimensions(self) -> int:
        """Return vector dimensions (1024 for v4)."""
        return 1024

    @lru_cache(maxsize=1000)
    async def _embed_stub_cached(
        self,
        texts: tuple[str, ...],
        input_type: str,
    ) -> tuple[tuple[float, ...], ...]:
        """Cached stub embed implementation.

        Args:
            texts: Tuple of text/base64 strings
            input_type: Input type for Cohere API (ignored in stub)

        Returns:
            Tuple of zero vector tuples

        """
        # TODO: Remove stub when embed-multimodal-v4.0 model is available
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"embed-multimodal-v4.0: returning {len(texts)} stub zero vectors (model not available)"
        )
        # Return zero vectors
        return tuple(tuple([0.0] * self.dimensions) for _ in texts)

    async def embed(
        self,
        content: list[str | bytes],
        input_type: str = "search_document",
    ) -> list[list[float]]:
        """Generate embedding vectors from batch of content.

        Args:
            content: List of text or image content to embed
            input_type: Purpose of embedding ("search_query" or "search_document")

        Returns:
            List of zero vectors (stub implementation)

        Note:
            Returns stub zero vectors until embed-multimodal-v4.0 is available.

        """
        # Prepare content for cache key (convert bytes to base64 strings)
        texts = []
        for item in content:
            if isinstance(item, str):
                if not item or not item.strip():
                    msg = "Content cannot be empty"
                    raise ValueError(msg)
                texts.append(item)
            elif isinstance(item, bytes):
                import base64
                encoded = base64.b64encode(item).decode("utf-8")
                texts.append(encoded)
            else:
                msg = f"Unsupported content type: {type(item)}"
                raise TypeError(msg)

        # Call cached stub version with tuple
        cached_result = await self._embed_stub_cached(tuple(texts), input_type)
        # Convert back to list of lists
        return [list(emb) for emb in cached_result]
