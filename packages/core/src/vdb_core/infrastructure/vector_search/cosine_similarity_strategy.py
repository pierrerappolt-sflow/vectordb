"""Cosine similarity strategy for nearest vector search."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .i_nearest_vector_strategy import INearestVectorStrategy

if TYPE_CHECKING:
    from vdb_core.domain.value_objects import Embedding


class CosineSimilarityStrategy(INearestVectorStrategy):
    """Nearest vector search using cosine similarity.

    Cosine similarity measures the cosine of the angle between two vectors,
    producing a value between -1 and 1:
    - 1.0: Identical direction (most similar)
    - 0.0: Orthogonal (unrelated)
    - -1.0: Opposite direction (least similar)

    Formula: similarity = dot(A, B) / (norm(A) * norm(B))

    This is ideal for text embeddings where magnitude is less important than direction.
    """

    def search(
        self,
        query_vector: tuple[float, ...],
        candidates: list[Embedding],
        top_k: int,
    ) -> list[tuple[Embedding, float]]:
        """Search for most similar embeddings using cosine similarity.

        Args:
            query_vector: The query vector to find neighbors for
            candidates: List of candidate embeddings to search through
            top_k: Number of top results to return

        Returns:
            List of (embedding, similarity_score) tuples, sorted by score descending.
            Similarity scores range from -1.0 to 1.0 (higher = more similar).

        """
        if not candidates:
            return []

        # Convert query to numpy array
        query_array = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query_array)

        # Avoid division by zero for zero vectors
        if query_norm == 0:
            return [(candidates[0], 0.0)] if candidates else []

        # Calculate cosine similarity for all candidates
        similarities: list[tuple[Embedding, float]] = []
        for embedding in candidates:
            candidate_array = np.array(embedding.vector, dtype=np.float32)
            candidate_norm = np.linalg.norm(candidate_array)

            # Handle zero vectors
            if candidate_norm == 0:
                similarity = 0.0
            else:
                # Cosine similarity: dot product / (norm(a) * norm(b))
                dot_product = np.dot(query_array, candidate_array)
                similarity = float(dot_product / (query_norm * candidate_norm))

            similarities.append((embedding, similarity))

        # Sort by similarity score (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
