"""NumPy in-memory vector store for similarity search."""

from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from vdb_core.domain.value_objects import VectorIndexingStrategy, VectorSimilarityMetric

logger = logging.getLogger(__name__)


class VectorIndex:
    """In-memory vector index using NumPy."""

    def __init__(
        self, dimensions: int, strategy: str, metric: VectorSimilarityMetric = VectorSimilarityMetric.L2
    ) -> None:
        """Initialize vector index.

        Args:
            dimensions: Vector dimensions
            strategy: Indexing strategy (FLAT, HNSW, IVF, PQ)
            metric: Similarity metric to use

        """
        self.dimensions = dimensions
        self.strategy = strategy
        self.metric = metric

        # Store vectors as numpy array
        self.vectors: NDArray[np.float32] | None = None  # Shape: (n_vectors, dimensions)
        self.embedding_ids: list[str] = []  # Embedding IDs in same order as vectors
        self.id_to_index: dict[str, int] = {}  # embedding_id -> index mapping

    def add(self, embedding_id: str, vector: list[float]) -> None:
        """Add vector to index.

        Args:
            embedding_id: UUID of embedding
            vector: Vector to add

        """
        if len(vector) != self.dimensions:
            msg = f"Vector dimension mismatch: expected {self.dimensions}, got {len(vector)}"
            raise ValueError(msg)

        # Convert to numpy array,
        # Handle compression here?
        vec_array = np.array(vector, dtype=np.float32).reshape(1, -1)  # Shape: (1, dimensions)

        if self.vectors is None:
            self.vectors = vec_array
        else:
            self.vectors = np.vstack([self.vectors, vec_array])

        idx = len(self.embedding_ids)
        self.embedding_ids.append(embedding_id)
        self.id_to_index[embedding_id] = idx

    def search(self, query_vector: list[float], k: int) -> tuple[list[str], list[float]]:
        """Search for k nearest neighbors.

        Args:
            query_vector: Query vector
            k: Number of results

        Returns:
            Tuple of (embedding_ids, scores)

        """
        if self.vectors is None or len(self.embedding_ids) == 0:
            return [], []

        query_array = np.array(query_vector, dtype=np.float32)  # Shape: (dimensions,)
        if self.metric == VectorSimilarityMetric.L2:
            raise NotImplementedError("L2 distance not implemented")

        elif self.metric == VectorSimilarityMetric.L1:
            raise NotImplementedError("L1 distance not implemented")

        elif self.metric == VectorSimilarityMetric.COSINE:
            query_norm = query_array / np.linalg.norm(query_array)
            # TODO: precomputing norms for all vectors and storing them?
            vectors_norm = self.vectors / np.linalg.norm(self.vectors, axis=1, keepdims=True)
            scores = np.dot(vectors_norm, query_norm)
            sorted_indices = np.argsort(scores)[::-1]

        elif self.metric == VectorSimilarityMetric.DOT_PRODUCT:
            raise NotImplementedError("Dot product not implemented")

        else:
            msg = f"Unknown similarity metric: {self.metric}"
            raise ValueError(msg)

        # Get top k results
        k = min(k, len(self.embedding_ids))
        top_k_indices = sorted_indices[:k]

        # Map back to embedding IDs and scores
        result_ids = [self.embedding_ids[int(idx)] for idx in top_k_indices]
        result_scores = [scores[idx].item() for idx in top_k_indices]

        return result_ids, result_scores

    def remove(self, embedding_id: str) -> bool:
        """Remove vector from index.

        Args:
            embedding_id: UUID of embedding to remove

        Returns:
            True if removed, False if not found

        """
        if embedding_id not in self.id_to_index:
            return False
        idx_to_remove = self.id_to_index[embedding_id]
        if self.vectors is not None:
            mask = np.ones(len(self.embedding_ids), dtype=bool)
            mask[idx_to_remove] = False
            self.vectors = self.vectors[mask]
            if self.vectors is not None and len(self.vectors) == 0:
                self.vectors = None
        self.embedding_ids.pop(idx_to_remove)
        self.id_to_index = {eid: i for i, eid in enumerate(self.embedding_ids)}

        return True

    @property
    def count(self) -> int:
        """Get number of vectors in index."""
        return len(self.embedding_ids)


class VectorIndexManager:
    """Manages in-memory vector indices per (library_id, config_id).

    Each (library_id, config_id) pair gets its own vector index, representing
    a unique combination of chunking + embedding strategies.
    """

    _instance: VectorIndexManager | None = None

    def __init__(self, metric: VectorSimilarityMetric = VectorSimilarityMetric.L2) -> None:
        """Initialize index manager.

        Args:
            metric: Default similarity metric to use

        """
        self.metric = metric
        self.indices: dict[tuple[str, str], VectorIndex] = {}  # (library_id, config_id) -> VectorIndex

    def get_or_create_index(
        self,
        library_id: str,
        config_id: str,
        dimensions: int,
        strategy: str,
        metric: VectorSimilarityMetric | None = None,
    ) -> VectorIndex:
        """Get or create index for (library_id, config_id) pair.

        Args:
            library_id: Library ID
            config_id: VectorizationConfig ID
            dimensions: Vector dimensions (from config's embedding strategy)
            strategy: Indexing strategy (from config)
            metric: Similarity metric to use (defaults to manager's metric if not provided)

        Returns:
            Vector index

        """
        key = (library_id, config_id)

        if key not in self.indices:
            # Use provided metric or fall back to manager's default
            index_metric = metric if metric is not None else self.metric
            self.indices[key] = self._create_index(dimensions, strategy, index_metric)
            logger.info(
                "Created %s index with %s metric for library=%s, config=%s, dimensions=%s",
                strategy,
                index_metric.value,
                library_id,
                config_id,
                dimensions,
            )

        return self.indices[key]

    def _create_index(
        self, dimensions: int, strategy: str, metric: VectorSimilarityMetric
    ) -> VectorIndex:
        """Create vector index based on strategy.

        Args:
            dimensions: Vector dimensions
            strategy: Indexing strategy string (flat, hnsw, ivf, pq)
            metric: Similarity metric to use for this index

        Returns:
            Vector index

        Note:
            Currently all strategies use FLAT (brute force) implementation.
            HNSW, IVF, and PQ are planned for future implementation.

        """
        # Normalize strategy to lowercase for comparison
        strategy_lower = strategy.lower()

        if strategy_lower == VectorIndexingStrategy.FLAT.value:
            # Brute force exact search using PyTorch tensors
            return VectorIndex(dimensions, strategy, metric)

        if strategy_lower == VectorIndexingStrategy.HNSW.value:
            # TODO: Implement HNSW (Hierarchical Navigable Small World) indexing
            # For now, use FLAT implementation
            logger.warning("HNSW not yet implemented - using FLAT for now")
            return VectorIndex(dimensions, VectorIndexingStrategy.FLAT.value, metric)

        if strategy_lower == VectorIndexingStrategy.IVF.value:
            # TODO: Implement IVF (Inverted File Index) indexing
            # For now, use FLAT implementation
            logger.warning("IVF not yet implemented - using FLAT for now")
            return VectorIndex(dimensions, VectorIndexingStrategy.FLAT.value, metric)

        if strategy_lower == VectorIndexingStrategy.PQ.value:
            # TODO: Implement PQ (Product Quantization) indexing
            # For now, use FLAT implementation
            logger.warning("PQ not yet implemented - using FLAT for now")
            return VectorIndex(dimensions, VectorIndexingStrategy.FLAT.value, metric)

        msg = f"Unknown indexing strategy: {strategy}"
        raise ValueError(msg)

    def add_vector(
        self,
        embedding_id: str,
        library_id: str,
        config_id: str,
        vector: list[float],
        dimensions: int,
        strategy: str,
        metric: VectorSimilarityMetric | None = None,
    ) -> None:
        """Add vector to appropriate index.

        Args:
            embedding_id: Embedding UUID
            library_id: Library UUID
            config_id: VectorizationConfig UUID
            vector: Vector to add
            dimensions: Vector dimensions
            strategy: Indexing strategy
            metric: Similarity metric (optional, uses manager default if not provided)

        """
        index = self.get_or_create_index(library_id, config_id, dimensions, strategy, metric)
        index.add(embedding_id, vector)

    def remove_vectors(
        self, library_id: str, config_id: str, embedding_ids: list[str]
    ) -> tuple[int, int]:
        """Remove vectors from appropriate index.

        Args:
            library_id: Library UUID
            config_id: VectorizationConfig UUID
            embedding_ids: List of embedding UUIDs to remove

        Returns:
            Tuple of (removed_count, not_found_count)

        """
        key = (library_id, config_id)

        if key not in self.indices:
            logger.warning("No index found for library=%s, config=%s", library_id, config_id)
            return 0, len(embedding_ids)

        index = self.indices[key]
        removed = 0
        not_found = 0

        for embedding_id in embedding_ids:
            if index.remove(embedding_id):
                removed += 1
            else:
                not_found += 1

        logger.info(
            "Removed %s embeddings from index (library=%s, config=%s), %s not found",
            removed,
            library_id,
            config_id,
            not_found,
        )

        return removed, not_found

    def search(
        self, library_id: str, config_id: str, query_vector: list[float], k: int = 10
    ) -> tuple[list[str], list[float]]:
        """Search for similar vectors within a (library, config) index.

        Args:
            library_id: Library UUID
            config_id: VectorizationConfig UUID
            query_vector: Query vector
            k: Number of results

        Returns:
            Tuple of (embedding_ids, scores)

        """
        key = (library_id, config_id)

        if key not in self.indices:
            logger.warning("No index found for library=%s, config=%s", library_id, config_id)
            return [], []

        return self.indices[key].search(query_vector, k)

    def get_stats(self) -> list[dict[str, object]]:
        """Get statistics for all indices.

        Returns:
            List of index statistics

        """
        return [
            {
                "library_id": lib_id,
                "config_id": cfg_id,
                "dimensions": idx.dimensions,
                "strategy": idx.strategy,
                "count": idx.count,
            }
            for (lib_id, cfg_id), idx in self.indices.items()
        ]

    async def bootstrap_from_postgres(self, database_url: str, batch_size: int = 1000) -> int:
        """Stream embeddings from postgres and build indices on cold start.

        Args:
            database_url: PostgreSQL connection string
            batch_size: Number of embeddings to fetch per batch

        Returns:
            Total number of embeddings indexed

        """
        import json

        import asyncpg

        logger.info("Starting bootstrap indexing from postgres...")

        pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
        if not pool:
            msg = "Failed to create postgres connection pool"
            raise RuntimeError(msg)

        try:
            offset = 0
            total_indexed = 0

            while True:
                rows = await pool.fetch(
                    """
                    SELECT e.id, e.library_id, e.vectorization_config_id, e.vector, e.dimensions,
                           vc.vector_indexing_strategy, vc.vector_similarity_metric
                    FROM embeddings e
                    JOIN vectorization_configs vc
                      ON e.vectorization_config_id = vc.id
                    ORDER BY e.library_id, e.vectorization_config_id
                    LIMIT $1 OFFSET $2
                    """,
                    batch_size,
                    offset,
                )

                if not rows:
                    break

                # Index batch
                for row in rows:
                    try:
                        # Parse JSONB vector
                        vector = json.loads(row["vector"]) if isinstance(row["vector"], str) else row["vector"]

                        # Parse similarity metric
                        similarity_metric = VectorSimilarityMetric(row["similarity_metric"])

                        self.add_vector(
                            embedding_id=str(row["id"]),
                            library_id=str(row["library_id"]),
                            config_id=str(row["vectorization_config_id"]),
                            vector=vector,
                            dimensions=row["dimensions"],
                            strategy=row["vector_indexing_strategy"],
                            metric=similarity_metric,
                        )
                        total_indexed += 1

                    except Exception as e:
                        logger.exception("Failed to index embedding %s: %s", row["id"], str(e))

                offset += batch_size
                logger.info("Indexed %s embeddings...", total_indexed)

            logger.info("Bootstrap complete. Total indexed: %s", total_indexed)
            return total_indexed

        finally:
            await pool.close()


class VectorIndexRegistry:
    """Registry managing VectorIndexManager instances per VectorizationConfig.

    Each VectorizationConfig gets its own VectorIndexManager with config-specific settings:
    - Similarity metric from config
    - Indexing strategy (FLAT, HNSW, IVF)
    - Dimensions determined by embedding strategy
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._managers: dict[str, VectorIndexManager] = {}

    def get_or_create_manager(
        self,
        config_id: str,
        metric: VectorSimilarityMetric = VectorSimilarityMetric.COSINE,
    ) -> VectorIndexManager:
        """Get or create VectorIndexManager for a VectorizationConfig.

        Args:
            config_id: VectorizationConfig ID
            metric: Similarity metric to use

        Returns:
            VectorIndexManager for this config

        """
        if config_id not in self._managers:
            self._managers[config_id] = VectorIndexManager(metric=metric)
            logger.info("Created VectorIndexManager for config %s with %s metric", config_id, metric.value)

        return self._managers[config_id]

    def get_manager(self, config_id: str) -> VectorIndexManager | None:
        """Get VectorIndexManager for a config, if it exists.

        Args:
            config_id: VectorizationConfig ID

        Returns:
            VectorIndexManager or None if not initialized

        """
        return self._managers.get(config_id)

    def remove_manager(self, config_id: str) -> None:
        """Remove VectorIndexManager for a config.

        Args:
            config_id: VectorizationConfig ID

        """
        if config_id in self._managers:
            del self._managers[config_id]
            logger.info("Removed VectorIndexManager for config %s", config_id)

    def get_stats(self) -> dict[str, list[dict[str, object]]]:
        """Get statistics for all managed indices.

        Returns:
            Dict mapping config_id to list of index stats

        """
        return {config_id: manager.get_stats() for config_id, manager in self._managers.items()}


# Global registry instance
_global_registry: VectorIndexRegistry | None = None


def get_vector_index_registry() -> VectorIndexRegistry:
    """Get or create the global VectorIndexRegistry singleton.

    Returns:
        Singleton VectorIndexRegistry instance

    """
    global _global_registry

    if _global_registry is None:
        _global_registry = VectorIndexRegistry()
        logger.info("Initialized global VectorIndexRegistry")

    return _global_registry
