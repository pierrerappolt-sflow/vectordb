"""In-memory vector repository implementation."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from vdb_core.domain.repositories import IEmbeddingReadRepository
from vdb_core.domain.value_objects import VectorIndexingStrategy
from vdb_core.infrastructure.vector_search import CosineSimilarityStrategy

if TYPE_CHECKING:
    from vdb_core.domain.value_objects import Embedding, EmbeddingId, LibraryId
    from vdb_core.infrastructure.vector_search.i_nearest_vector_strategy import INearestVectorStrategy


class InMemoryEmbeddingReadRepository(IEmbeddingReadRepository):
    """In-memory vector storage with strategy-based similarity search.

    Storage structure:
    - Embeddings grouped by LibraryId for isolated library search
    - Strategy resolver maps VectorIndexingStrategy enum to concrete implementations

    This is useful for:
    - Testing
    - Development
    - Small datasets that fit in memory
    """

    def __init__(
        self,
        strategy_resolver: dict[VectorIndexingStrategy, INearestVectorStrategy] | None = None,
    ) -> None:
        """Initialize the in-memory vector repository.

        Args:
            strategy_resolver: Maps VectorIndexingStrategy to concrete implementations.
                             Defaults to {COSINE_SIMILARITY: CosineSimilarityStrategy()}

        """
        # Storage: library_id -> list of embeddings
        self._storage: dict[LibraryId, list[Embedding]] = defaultdict(list)

        # Strategy resolver with default
        if strategy_resolver is None:
            self._strategy_resolver: dict[VectorIndexingStrategy, INearestVectorStrategy] = {
                VectorIndexingStrategy.FLAT: CosineSimilarityStrategy()
            }
        else:
            self._strategy_resolver = strategy_resolver

    async def add_embeddings(
        self,
        embeddings: list[Embedding],
        library_id: LibraryId,
    ) -> None:
        """Add multiple embeddings to the vector index for a library.

        Args:
            embeddings: List of embeddings to index
            library_id: Library these embeddings belong to

        """
        if not embeddings:
            return

        # Batch append to library's embedding list
        self._storage[library_id].extend(embeddings)

    async def remove_embeddings(
        self,
        embedding_ids: list[EmbeddingId],
        library_id: LibraryId,
    ) -> None:
        """Remove multiple embeddings from the vector index.

        Args:
            embedding_ids: IDs of embeddings to remove
            library_id: Library to remove embeddings from

        """
        if not embedding_ids or library_id not in self._storage:
            return

        # Convert to set for O(1) lookup
        ids_to_remove = set(embedding_ids)

        # Filter out embeddings with matching IDs
        self._storage[library_id] = [emb for emb in self._storage[library_id] if emb.embedding_id not in ids_to_remove]

        # Clean up empty library entries
        if not self._storage[library_id]:
            del self._storage[library_id]

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
            strategy: Similarity algorithm to use

        Returns:
            List of (embedding, similarity_score) tuples, sorted by score descending.

        Raises:
            ValueError: If the specified strategy is not configured

        """
        # Get embeddings for this library
        candidates = self._storage.get(library_id, [])
        if not candidates:
            return []

        # Resolve strategy
        strategy_impl = self._strategy_resolver.get(strategy)
        if strategy_impl is None:
            msg = f"Strategy {strategy} not configured in resolver"
            raise ValueError(msg)

        # Delegate to strategy for similarity computation
        return strategy_impl.search(query_vector, candidates, top_k)

    def clear(self, library_id: LibraryId | None = None) -> None:
        """Clear all embeddings for a library or all libraries.

        Args:
            library_id: If provided, clear only this library. If None, clear all.

        Note:
            This is a utility method for testing, not part of IEmbeddingReadRepository.

        """
        if library_id is None:
            self._storage.clear()
        elif library_id in self._storage:
            del self._storage[library_id]

    def get_embedding_count(self, library_id: LibraryId) -> int:
        """Get the number of embeddings indexed for a library.

        Args:
            library_id: Library to count embeddings for

        Returns:
            Number of embeddings indexed

        Note:
            This is a utility method for testing, not part of IEmbeddingReadRepository.

        """
        return len(self._storage.get(library_id, []))
