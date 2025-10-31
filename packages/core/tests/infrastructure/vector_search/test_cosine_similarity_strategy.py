"""Tests for CosineSimilarityStrategy."""

from uuid import uuid4

import pytest
from vdb_core.domain.value_objects import (
    ChunkId,
    Embedding,
    EmbeddingStrategyId,
    VectorizationConfigId,
)
from vdb_core.infrastructure.vector_search import CosineSimilarityStrategy


class TestCosineSimilarityStrategy:
    """Test suite for CosineSimilarityStrategy."""

    @pytest.fixture
    def strategy(self) -> CosineSimilarityStrategy:
        """Create a CosineSimilarityStrategy instance."""
        return CosineSimilarityStrategy()

    @pytest.fixture
    def sample_embeddings(self) -> list[Embedding]:
        """Create sample embeddings for testing."""
        strategy_id = EmbeddingStrategyId(uuid4())
        library_id = uuid4()
        config_id = VectorizationConfigId(uuid4())
        chunk1 = ChunkId("chunk1")
        chunk2 = ChunkId("chunk2")
        chunk3 = ChunkId("chunk3")

        return [
            Embedding(
                chunk_id=chunk1,
                embedding_strategy_id=strategy_id,
                vector=(1.0, 0.0, 0.0),  # Orthogonal to (0,1,0)
                library_id=library_id,
                vectorization_config_id=config_id,
            ),
            Embedding(
                chunk_id=chunk2,
                embedding_strategy_id=strategy_id,
                vector=(0.0, 1.0, 0.0),  # Orthogonal to (1,0,0)
                library_id=library_id,
                vectorization_config_id=config_id,
            ),
            Embedding(
                chunk_id=chunk3,
                embedding_strategy_id=strategy_id,
                vector=(0.7071, 0.7071, 0.0),  # 45 degrees from (1,0,0)
                library_id=library_id,
                vectorization_config_id=config_id,
            ),
        ]

    def test_identical_vectors_have_similarity_one(self, strategy: CosineSimilarityStrategy) -> None:
        """Test that identical vectors have cosine similarity of 1.0."""
        query = (1.0, 0.0, 0.0)
        strategy_id = EmbeddingStrategyId(uuid4())
        chunk_id = ChunkId("identical")
        library_id = uuid4()
        config_id = VectorizationConfigId(uuid4())
        candidates = [
            Embedding(
                chunk_id=chunk_id,
                embedding_strategy_id=strategy_id,
                vector=(1.0, 0.0, 0.0),
                library_id=library_id,
                vectorization_config_id=config_id,
            )
        ]

        results = strategy.search(query, candidates, top_k=1)

        assert len(results) == 1
        assert results[0][1] == pytest.approx(1.0)

    def test_orthogonal_vectors_have_similarity_zero(self, strategy: CosineSimilarityStrategy) -> None:
        """Test that orthogonal vectors have cosine similarity of 0.0."""
        query = (1.0, 0.0, 0.0)
        strategy_id = EmbeddingStrategyId(uuid4())
        chunk_id = ChunkId("orthogonal")
        library_id = uuid4()
        config_id = VectorizationConfigId(uuid4())
        candidates = [
            Embedding(
                chunk_id=chunk_id,
                embedding_strategy_id=strategy_id,
                vector=(0.0, 1.0, 0.0),
                library_id=library_id,
                vectorization_config_id=config_id,
            )
        ]

        results = strategy.search(query, candidates, top_k=1)

        assert len(results) == 1
        assert results[0][1] == pytest.approx(0.0)

    def test_opposite_vectors_have_negative_similarity(self, strategy: CosineSimilarityStrategy) -> None:
        """Test that opposite vectors have cosine similarity of -1.0."""
        query = (1.0, 0.0, 0.0)
        strategy_id = EmbeddingStrategyId(uuid4())
        chunk_id = ChunkId("opposite")
        library_id = uuid4()
        config_id = VectorizationConfigId(uuid4())
        candidates = [
            Embedding(
                chunk_id=chunk_id,
                embedding_strategy_id=strategy_id,
                vector=(-1.0, 0.0, 0.0),
                library_id=library_id,
                vectorization_config_id=config_id,
            )
        ]

        results = strategy.search(query, candidates, top_k=1)

        assert len(results) == 1
        assert results[0][1] == pytest.approx(-1.0)

    def test_results_sorted_by_similarity_descending(
        self, strategy: CosineSimilarityStrategy, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that results are sorted by similarity score in descending order."""
        query = (1.0, 0.0, 0.0)

        results = strategy.search(query, sample_embeddings, top_k=3)

        assert len(results) == 3
        # First result should be (1,0,0) with similarity 1.0
        assert results[0][0].vector == (1.0, 0.0, 0.0)
        assert results[0][1] == pytest.approx(1.0)

        # Second result should be (0.7071, 0.7071, 0) with similarity ~0.7071
        assert results[1][0].vector == (0.7071, 0.7071, 0.0)
        assert results[1][1] == pytest.approx(0.7071, abs=0.001)

        # Third result should be (0,1,0) with similarity 0.0
        assert results[2][0].vector == (0.0, 1.0, 0.0)
        assert results[2][1] == pytest.approx(0.0)

    def test_top_k_limits_results(self, strategy: CosineSimilarityStrategy, sample_embeddings: list[Embedding]) -> None:
        """Test that top_k parameter limits the number of results."""
        query = (1.0, 0.0, 0.0)

        results = strategy.search(query, sample_embeddings, top_k=2)

        assert len(results) == 2

    def test_empty_candidates_returns_empty_list(self, strategy: CosineSimilarityStrategy) -> None:
        """Test that searching with no candidates returns empty list."""
        query = (1.0, 0.0, 0.0)

        results = strategy.search(query, [], top_k=5)

        assert results == []

    def test_zero_query_vector_returns_first_candidate(
        self, strategy: CosineSimilarityStrategy, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that a zero query vector returns the first candidate with score 0.0."""
        query = (0.0, 0.0, 0.0)

        results = strategy.search(query, sample_embeddings, top_k=1)

        assert len(results) == 1
        assert results[0][1] == 0.0

    def test_zero_candidate_vector_has_zero_similarity(self, strategy: CosineSimilarityStrategy) -> None:
        """Test that a candidate with zero vector has similarity 0.0."""
        query = (1.0, 0.0, 0.0)
        strategy_id = EmbeddingStrategyId(uuid4())
        chunk_id = ChunkId("zero")
        library_id = uuid4()
        config_id = VectorizationConfigId(uuid4())
        candidates = [
            Embedding(
                chunk_id=chunk_id,
                embedding_strategy_id=strategy_id,
                vector=(0.0, 0.0, 0.0),
                library_id=library_id,
                vectorization_config_id=config_id,
            )
        ]

        results = strategy.search(query, candidates, top_k=1)

        assert len(results) == 1
        assert results[0][1] == 0.0

    def test_high_dimensional_vectors(self, strategy: CosineSimilarityStrategy) -> None:
        """Test cosine similarity with high-dimensional vectors."""
        # 1536 dimensions (like OpenAI ada-002)
        query = tuple([1.0] + [0.0] * 1535)
        strategy_id = EmbeddingStrategyId(uuid4())
        chunk_id = ChunkId("high_dim")
        library_id = uuid4()
        config_id = VectorizationConfigId(uuid4())
        candidates = [
            Embedding(
                chunk_id=chunk_id,
                embedding_strategy_id=strategy_id,
                vector=tuple([1.0] + [0.0] * 1535),
                library_id=library_id,
                vectorization_config_id=config_id,
            )
        ]

        results = strategy.search(query, candidates, top_k=1)

        assert len(results) == 1
        assert results[0][1] == pytest.approx(1.0)
