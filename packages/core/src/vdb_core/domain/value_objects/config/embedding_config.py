"""EmbeddingConfig - configuration for embedding services.

LEGACY: This is infrastructure configuration used by old embedding services.
New code should use EmbeddingStrategy entities instead.
"""

from typing import final

from pydantic.dataclasses import dataclass

from .embedding_provider import EmbeddingProvider


@final
@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    """Configuration for embedding service (legacy).

    Used by infrastructure embedding services (CohereEmbeddingService, etc.)
    to configure API access and model selection.

    This is legacy infrastructure config. Domain logic should use
    EmbeddingStrategy entities from the domain/entities/strategies/ folder.

    Attributes:
        provider: Which embedding API provider to use
        model: Model identifier (e.g., "embed-english-v3.0" for Cohere)
        dimension: Embedding vector dimensionality
        api_key: API key for the provider (optional, can use env vars)

    Example:
        config = EmbeddingConfig(
            provider=EmbeddingProvider.COHERE,
            model="embed-english-v3.0",
            dimension=1024,
            api_key="your-api-key"
        )

    """

    provider: EmbeddingProvider
    model: str
    dimension: int
    api_key: str | None = None
