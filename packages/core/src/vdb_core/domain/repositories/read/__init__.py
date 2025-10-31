"""Read-side repositories for CQRS pattern."""

from .i_chunk_read_repository import IChunkReadRepository
from .i_embedding_read_repository import IEmbeddingReadRepository

__all__ = [
    "IChunkReadRepository",
    "IEmbeddingReadRepository",
]
