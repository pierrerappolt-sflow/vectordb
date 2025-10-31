"""Domain repository interfaces.

Following DDD principles:
- Aggregate roots have repositories: Library, VectorizationConfig
- Documents, Chunks, Embeddings, etc. are written through Library aggregate
- ChunkingStrategy, EmbeddingStrategy are written through VectorizationConfig aggregate

CQRS Read Repositories:
- IEmbeddingReadRepository is a query-side repository for semantic search
  (optimized for similarity search, NOT traditional CRUD)
- IChunkReadRepository is a query-side repository for chunk lookups
  (read-only, chunks written through Library aggregate)
"""

from vdb_core.domain.base import AbstractRepository

from .i_library_repository import ILibraryRepository
from .i_strategy_repositories import IVectorizationConfigRepository
from .read import IChunkReadRepository, IEmbeddingReadRepository

__all__ = [
    "AbstractRepository",
    "IChunkReadRepository",
    "IEmbeddingReadRepository",
    "ILibraryRepository",
    "IVectorizationConfigRepository",
]
