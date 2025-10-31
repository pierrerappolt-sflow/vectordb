"""EmbeddingConfig (legacy)."""

from typing import final

from pydantic.dataclasses import dataclass

from .embedding_provider import EmbeddingProvider


@final
@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    """Config for embedding service (legacy)."""

    provider: EmbeddingProvider
    model: str
    dimension: int
    api_key: str | None = None
