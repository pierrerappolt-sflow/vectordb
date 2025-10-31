"""Nearest vector search strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vdb_core.domain.value_objects import Embedding


class INearestVectorStrategy(ABC):
    """Strategy interface for nearest vector search algorithms.

    Different implementations provide different similarity/distance metrics:
    - Cosine similarity (angle-based)
    - Euclidean distance (L2 norm)
    - Dot product similarity
    - etc.

    The strategy pattern allows swapping algorithms without changing client code.
    """

    @abstractmethod
    def search(
        self,
        query_vector: tuple[float, ...],
        candidates: list[Embedding],
        top_k: int,
    ) -> list[tuple[Embedding, float]]:
        """Search for nearest vectors among candidates.

        Args:
            query_vector: The query vector to find neighbors for
            candidates: List of candidate embeddings to search through
            top_k: Number of top results to return

        Returns:
            List of (embedding, score) tuples, sorted by score (descending).
            Higher scores indicate greater similarity/closer distance.

        Example:
            strategy = CosineSimilarityStrategy()
            results = strategy.search(query_vec, all_embeddings, top_k=5)
            # [(embedding1, 0.95), (embedding2, 0.87), ...]

        """
