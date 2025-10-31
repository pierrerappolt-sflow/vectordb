"""Embedding read repository interface - CQRS read model for semantic search."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vdb_core.domain.value_objects import Embedding, EmbeddingId, LibraryId, VectorIndexingStrategy


class IEmbeddingReadRepository(ABC):
    """CQRS Read Repository for embedding similarity search.

    This is a QUERY-SIDE repository optimized for vector similarity search.
    NOT a traditional domain repository for CRUD operations.

    CQRS Separation:
    - Write path: Library aggregate → Embeddings → Domain events → Async indexing
    - Read path: This repository (optimized for semantic search)

    Specializes in:
    - Batch indexing operations (eventual consistency)
    - Similarity search with configurable strategies (cosine, L2, etc.)
    - Library-scoped vector indices

    Note: NOT part of Unit of Work pattern. Vector operations are eventually
    consistent and optimized for read performance.
    """

    @abstractmethod
    async def add_embeddings(
        self,
        embeddings: list[Embedding],
        library_id: LibraryId,
    ) -> None:
        """Add multiple embeddings to the vector index for a library.

        Args:
            embeddings: List of embeddings to index
            library_id: Library these embeddings belong to

        Raises:
            ValidationException: If embeddings have mismatched dimensions

        """

    @abstractmethod
    async def remove_embeddings(
        self,
        embedding_ids: list[EmbeddingId],
        library_id: LibraryId,
    ) -> None:
        """Remove multiple embeddings from the vector index.

        Args:
            embedding_ids: IDs of embeddings to remove
            library_id: Library to remove embeddings from

        Note:
            Silently ignores IDs that don't exist in the index.

        """

    @abstractmethod
    async def search_similar(
        self,
        query_vector: tuple[float, ...],
        library_id: LibraryId,
        top_k: int,
        strategy: VectorIndexingStrategy,
    ) -> list[tuple[Embedding, float]]:
        """Search for similar embeddings in a library's vector index.

        Args:
            query_vector: The vector to find similar embeddings for
            library_id: Library to search within
            top_k: Maximum number of results to return
            strategy: Vector indexing strategy to use (e.g., FLAT for brute-force search)

        Returns:
            List of (embedding, similarity_score) tuples, sorted by score descending.
            Returns fewer than top_k if library has fewer embeddings.

        Example:
            results = await repo.search_similar(
                query_vector=(0.1, 0.2, 0.3, ...),
                library_id=library_id,
                top_k=5,
                strategy=VectorIndexingStrategy.FLAT
            )
            # [(embedding1, 0.95), (embedding2, 0.87), ...]

        """
