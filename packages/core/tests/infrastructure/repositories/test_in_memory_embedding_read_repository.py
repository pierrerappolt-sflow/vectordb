"""Tests for InMemoryEmbeddingReadRepository."""

from uuid import uuid4

import pytest
from vdb_core.domain.value_objects import (
    ChunkId,
    Embedding,
    EmbeddingId,
    EmbeddingStrategyId,
    LibraryId,
    VectorIndexingStrategy,
    VectorizationConfigId,
)
from vdb_core.infrastructure.repositories import InMemoryEmbeddingReadRepository
from vdb_core.infrastructure.vector_search import CosineSimilarityStrategy


class TestInMemoryEmbeddingReadRepository:
    """Test suite for InMemoryEmbeddingReadRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryEmbeddingReadRepository:
        """Create an InMemoryEmbeddingReadRepository instance."""
        return InMemoryEmbeddingReadRepository()

    @pytest.fixture
    def library_id(self) -> LibraryId:
        """Create a test library ID."""
        return uuid4()

    @pytest.fixture
    def sample_embeddings(self, library_id: LibraryId) -> list[Embedding]:
        """Create sample embeddings for testing."""
        strategy_id = EmbeddingStrategyId(uuid4())
        config_id = VectorizationConfigId(uuid4())
        chunk1 = ChunkId("chunk1")
        chunk2 = ChunkId("chunk2")
        chunk3 = ChunkId("chunk3")

        return [
            Embedding(
                chunk_id=chunk1,
                embedding_strategy_id=strategy_id,
                vector=(1.0, 0.0, 0.0),
                library_id=library_id,
                vectorization_config_id=config_id,
            ),
            Embedding(
                chunk_id=chunk2,
                embedding_strategy_id=strategy_id,
                vector=(0.0, 1.0, 0.0),
                library_id=library_id,
                vectorization_config_id=config_id,
            ),
            Embedding(
                chunk_id=chunk3,
                embedding_strategy_id=strategy_id,
                vector=(0.7071, 0.7071, 0.0),
                library_id=library_id,
                vectorization_config_id=config_id,
            ),
        ]

    async def test_add_embeddings_to_library(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId, sample_embeddings: list[Embedding]
    ) -> None:
        """Test adding embeddings to a library."""
        await repository.add_embeddings(sample_embeddings, library_id)

        count = repository.get_embedding_count(library_id)
        assert count == 3

    async def test_add_empty_list_does_nothing(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId
    ) -> None:
        """Test that adding an empty list doesn't create a library entry."""
        await repository.add_embeddings([], library_id)

        count = repository.get_embedding_count(library_id)
        assert count == 0

    async def test_add_embeddings_multiple_times_appends(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that multiple add operations append embeddings."""
        await repository.add_embeddings(sample_embeddings[:2], library_id)
        await repository.add_embeddings(sample_embeddings[2:], library_id)

        count = repository.get_embedding_count(library_id)
        assert count == 3

    async def test_remove_embeddings_by_id(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId, sample_embeddings: list[Embedding]
    ) -> None:
        """Test removing embeddings by their IDs."""
        await repository.add_embeddings(sample_embeddings, library_id)

        # Remove first two embeddings
        ids_to_remove = [sample_embeddings[0].embedding_id, sample_embeddings[1].embedding_id]
        await repository.remove_embeddings(ids_to_remove, library_id)

        count = repository.get_embedding_count(library_id)
        assert count == 1

    async def test_remove_nonexistent_embeddings_silently_ignored(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that removing non-existent IDs doesn't raise an error."""
        await repository.add_embeddings(sample_embeddings, library_id)

        # Try to remove non-existent ID
        fake_chunk = ChunkId("fake")
        fake_strategy = EmbeddingStrategyId(uuid4())
        fake_id = EmbeddingId.from_chunk_and_strategy(fake_chunk, fake_strategy)
        await repository.remove_embeddings([fake_id], library_id)

        count = repository.get_embedding_count(library_id)
        assert count == 3  # Nothing removed

    async def test_remove_from_nonexistent_library_silently_ignored(
        self, repository: InMemoryEmbeddingReadRepository
    ) -> None:
        """Test that removing from non-existent library doesn't raise an error."""
        fake_library_id = uuid4()
        fake_chunk = ChunkId("fake")
        fake_strategy = EmbeddingStrategyId(uuid4())
        fake_embedding_id = EmbeddingId.from_chunk_and_strategy(fake_chunk, fake_strategy)

        # Should not raise
        await repository.remove_embeddings([fake_embedding_id], fake_library_id)

    async def test_remove_all_embeddings_cleans_up_library_entry(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that removing all embeddings cleans up the library entry."""
        await repository.add_embeddings(sample_embeddings, library_id)

        # Remove all embeddings
        all_ids = [emb.embedding_id for emb in sample_embeddings]
        await repository.remove_embeddings(all_ids, library_id)

        count = repository.get_embedding_count(library_id)
        assert count == 0

    async def test_search_similar_returns_top_k_results(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that search_similar returns top_k most similar embeddings."""
        await repository.add_embeddings(sample_embeddings, library_id)

        query_vector = (1.0, 0.0, 0.0)
        results = await repository.search_similar(
            query_vector, library_id, top_k=2, strategy=VectorIndexingStrategy.FLAT
        )

        assert len(results) == 2
        # Most similar should be (1,0,0)
        assert results[0][0].vector == (1.0, 0.0, 0.0)
        assert results[0][1] == pytest.approx(1.0)

    async def test_search_empty_library_returns_empty_list(
        self, repository: InMemoryEmbeddingReadRepository, library_id: LibraryId
    ) -> None:
        """Test that searching an empty library returns empty list."""
        query_vector = (1.0, 0.0, 0.0)

        results = await repository.search_similar(
            query_vector, library_id, top_k=5, strategy=VectorIndexingStrategy.FLAT
        )

        assert results == []

    async def test_search_nonexistent_library_returns_empty_list(
        self, repository: InMemoryEmbeddingReadRepository
    ) -> None:
        """Test that searching a non-existent library returns empty list."""
        fake_library_id = uuid4()
        query_vector = (1.0, 0.0, 0.0)

        results = await repository.search_similar(
            query_vector, fake_library_id, top_k=5, strategy=VectorIndexingStrategy.FLAT
        )

        assert results == []

    async def test_search_with_unconfigured_strategy_raises_error(
        self, library_id: LibraryId, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that using an unconfigured strategy raises ValueError."""
        # Create repository with empty strategy resolver
        repository = InMemoryEmbeddingReadRepository(strategy_resolver={})
        await repository.add_embeddings(sample_embeddings, library_id)

        query_vector = (1.0, 0.0, 0.0)

        with pytest.raises(ValueError, match="Strategy .* not configured in resolver"):
            await repository.search_similar(query_vector, library_id, top_k=5, strategy=VectorIndexingStrategy.FLAT)

    async def test_custom_strategy_resolver(self, library_id: LibraryId, sample_embeddings: list[Embedding]) -> None:
        """Test repository can be configured with custom strategy resolver."""
        from vdb_core.infrastructure.vector_search.i_nearest_vector_strategy import INearestVectorStrategy

        custom_resolver: dict[VectorIndexingStrategy, INearestVectorStrategy] = {
            VectorIndexingStrategy.FLAT: CosineSimilarityStrategy()
        }
        repository = InMemoryEmbeddingReadRepository(strategy_resolver=custom_resolver)

        await repository.add_embeddings(sample_embeddings, library_id)

        query_vector = (1.0, 0.0, 0.0)
        results = await repository.search_similar(
            query_vector, library_id, top_k=1, strategy=VectorIndexingStrategy.FLAT
        )

        assert len(results) == 1

    async def test_different_libraries_isolated(
        self, repository: InMemoryEmbeddingReadRepository, sample_embeddings: list[Embedding]
    ) -> None:
        """Test that embeddings in different libraries are isolated."""
        library1 = uuid4()
        library2 = uuid4()

        await repository.add_embeddings(sample_embeddings[:2], library1)
        await repository.add_embeddings(sample_embeddings[2:], library2)

        assert repository.get_embedding_count(library1) == 2
        assert repository.get_embedding_count(library2) == 1

        # Search library1 should only find embeddings from library1
        query_vector = (1.0, 0.0, 0.0)
        results = await repository.search_similar(
            query_vector, library1, top_k=10, strategy=VectorIndexingStrategy.FLAT
        )

        assert len(results) == 2  # Only library1's embeddings

    async def test_clear_specific_library(
        self, repository: InMemoryEmbeddingReadRepository, sample_embeddings: list[Embedding]
    ) -> None:
        """Test clearing embeddings for a specific library."""
        library1 = uuid4()
        library2 = uuid4()

        await repository.add_embeddings(sample_embeddings[:2], library1)
        await repository.add_embeddings(sample_embeddings[2:], library2)

        repository.clear(library1)

        assert repository.get_embedding_count(library1) == 0
        assert repository.get_embedding_count(library2) == 1

    async def test_clear_all_libraries(
        self, repository: InMemoryEmbeddingReadRepository, sample_embeddings: list[Embedding]
    ) -> None:
        """Test clearing all embeddings across all libraries."""
        library1 = uuid4()
        library2 = uuid4()

        await repository.add_embeddings(sample_embeddings[:2], library1)
        await repository.add_embeddings(sample_embeddings[2:], library2)

        repository.clear()

        assert repository.get_embedding_count(library1) == 0
        assert repository.get_embedding_count(library2) == 0
