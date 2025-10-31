"""Embedding-related value objects."""

from pydantic.dataclasses import rebuild_dataclass

from .embed_input_type import EmbedInputType
from .embedding import Embedding
from .embedding_id import EmbeddingId
from .vector_indexing_strategy import VectorIndexingStrategy
from .vector_similarity_metric import VectorSimilarityMetric

# Rebuild Embedding dataclass to resolve forward references
rebuild_dataclass(Embedding)  # type: ignore[arg-type]

__all__ = [
    "Embedding",
    "EmbeddingId",
    "VectorIndexingStrategy",
    "VectorSimilarityMetric",
    "EmbedInputType",
]
