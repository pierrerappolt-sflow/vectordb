"""Tests for search-related Temporal activities."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from vdb_core.application.read_models import ChunkReadModel
from vdb_core.domain.value_objects import ChunkId
from vdb_core.infrastructure.activities.search_activities import (
    enrich_search_results_activity,
    generate_query_embedding_activity,
    search_vectors_activity,
)


@pytest.mark.asyncio
class TestGenerateQueryEmbeddingActivity:
    """Tests for generate_query_embedding_activity.

    Note: This activity has a known bug - it tries to instantiate Chunk with TYPE_CHECKING imports.
    These tests document the expected behavior once the bug is fixed.
    """

    @patch("vdb_core.infrastructure.activities.search_activities.Chunk")
    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_generates_embedding_for_query_text(
        self, mock_get_container: MagicMock, mock_chunk_class: MagicMock
    ) -> None:
        """Test that activity generates embedding vector for query text."""
        # Arrange
        library_id = str(uuid4())
        query_text = "What is machine learning?"
        expected_vector = [0.1] * 1024  # Mock 1024-dim vector

        # Mock chunk instance
        mock_chunk = MagicMock()
        mock_chunk_class.return_value = mock_chunk

        # Mock DI container and embedding service
        mock_container = MagicMock()
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding = AsyncMock(
            return_value=expected_vector
        )
        mock_container.get_embedding_service = MagicMock(
            return_value=mock_embedding_service
        )
        mock_get_container.return_value = mock_container

        # Act
        result = await generate_query_embedding_activity(
            query_text=query_text,
            library_id=library_id,
        )

        # Assert
        assert result == expected_vector
        assert len(result) == 1024
        mock_embedding_service.generate_embedding.assert_called_once()

    @patch("vdb_core.infrastructure.activities.search_activities.Chunk")
    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_uses_search_input_type_for_embedding(
        self, mock_get_container: MagicMock, mock_chunk_class: MagicMock
    ) -> None:
        """Test that activity uses SEARCH input type for query embeddings."""
        # Arrange
        library_id = str(uuid4())
        query_text = "Test query"

        mock_chunk = MagicMock()
        mock_chunk_class.return_value = mock_chunk

        mock_container = MagicMock()
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding = AsyncMock(return_value=[0.1] * 1024)
        mock_container.get_embedding_service = MagicMock(
            return_value=mock_embedding_service
        )
        mock_get_container.return_value = mock_container

        # Act
        await generate_query_embedding_activity(
            query_text=query_text,
            library_id=library_id,
        )

        # Assert
        call_args = mock_embedding_service.generate_embedding.call_args
        input_type = call_args[0][2]  # Third argument is input_type
        assert input_type.value == "search"

    @patch("vdb_core.infrastructure.activities.search_activities.Chunk")
    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_handles_long_query_text(
        self, mock_get_container: MagicMock, mock_chunk_class: MagicMock
    ) -> None:
        """Test that activity handles long query text correctly."""
        # Arrange
        library_id = str(uuid4())
        # Create a long query (1000 characters)
        query_text = "machine learning " * 60

        mock_chunk = MagicMock()
        mock_chunk_class.return_value = mock_chunk

        mock_container = MagicMock()
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embedding = AsyncMock(return_value=[0.1] * 1024)
        mock_container.get_embedding_service = MagicMock(
            return_value=mock_embedding_service
        )
        mock_get_container.return_value = mock_container

        # Act
        result = await generate_query_embedding_activity(
            query_text=query_text,
            library_id=library_id,
        )

        # Assert
        assert result is not None
        assert len(result) == 1024


@pytest.mark.asyncio
class TestSearchVectorsActivity:
    """Tests for search_vectors_activity."""

    @patch("vdb_core.infrastructure.activities.search_activities.httpx.AsyncClient")
    async def test_calls_search_service_with_correct_parameters(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test that activity makes HTTP request to search service with correct params."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_vector = [0.1] * 1024
        top_k = 10

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "embedding_id": str(uuid4()),
                    "chunk_id": str(uuid4()),
                    "distance": 0.95,
                },
                {
                    "embedding_id": str(uuid4()),
                    "chunk_id": str(uuid4()),
                    "distance": 0.92,
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        # Mock async client
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Act
        result = await search_vectors_activity(
            library_id=library_id,
            config_id=config_id,
            query_vector=query_vector,
            top_k=top_k,
        )

        # Assert
        assert len(result) == 2
        assert result[0]["score"] == 0.95
        assert result[1]["score"] == 0.92

        # Verify HTTP request was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/search" in call_args[0][0]
        assert call_args[1]["json"]["library_id"] == library_id
        assert call_args[1]["json"]["config_id"] == config_id
        assert call_args[1]["json"]["query_vector"] == query_vector
        assert call_args[1]["json"]["k"] == top_k

    @patch("vdb_core.infrastructure.activities.search_activities.httpx.AsyncClient")
    async def test_handles_empty_search_results(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test that activity handles empty search results gracefully."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_vector = [0.1] * 1024
        top_k = 10

        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Act
        result = await search_vectors_activity(
            library_id=library_id,
            config_id=config_id,
            query_vector=query_vector,
            top_k=top_k,
        )

        # Assert
        assert result == []

    @patch("vdb_core.infrastructure.activities.search_activities.httpx.AsyncClient")
    async def test_raises_on_http_error(self, mock_client_class: MagicMock) -> None:
        """Test that activity raises exception on HTTP error."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_vector = [0.1] * 1024
        top_k = 10

        # Create actual HTTPStatusError
        http_error = httpx.HTTPStatusError(
            "Service unavailable",
            request=MagicMock(),
            response=MagicMock(status_code=503),
        )

        # Mock HTTP error response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = http_error

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_class.return_value = mock_client

        # Act & Assert
        with pytest.raises(httpx.HTTPStatusError):
            await search_vectors_activity(
                library_id=library_id,
                config_id=config_id,
                query_vector=query_vector,
                top_k=top_k,
            )

    @patch("vdb_core.infrastructure.activities.search_activities.httpx.AsyncClient")
    async def test_uses_environment_search_service_url(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test that activity uses SEARCH_SERVICE_URL from environment."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_vector = [0.1] * 1024
        top_k = 5

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Act
        with patch.dict("os.environ", {"SEARCH_SERVICE_URL": "http://custom-search:9000"}):
            await search_vectors_activity(
                library_id=library_id,
                config_id=config_id,
                query_vector=query_vector,
                top_k=top_k,
            )

        # Assert - verify custom URL was used
        call_args = mock_client.post.call_args
        assert call_args[0][0].startswith("http://custom-search:9000")

    @patch("vdb_core.infrastructure.activities.search_activities.httpx.AsyncClient")
    async def test_sets_request_timeout(self, mock_client_class: MagicMock) -> None:
        """Test that activity sets proper timeout for HTTP requests."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_vector = [0.1] * 1024
        top_k = 10

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        # Act
        await search_vectors_activity(
            library_id=library_id,
            config_id=config_id,
            query_vector=query_vector,
            top_k=top_k,
        )

        # Assert - verify timeout was set
        call_args = mock_client.post.call_args
        assert call_args[1]["timeout"] == 30.0


@pytest.mark.asyncio
class TestEnrichSearchResultsActivity:
    """Tests for enrich_search_results_activity."""

    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_enriches_results_with_chunk_details(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity enriches search results with chunk details."""
        # Arrange
        from datetime import UTC, datetime

        chunk_id = ChunkId(str(uuid4()))
        document_id = uuid4()
        embedding_id = str(uuid4())

        raw_results = [
            {
                "embedding_id": embedding_id,
                "chunk_id": str(chunk_id),
                "score": 0.95,
            }
        ]

        # Mock chunk read model
        mock_chunk = ChunkReadModel(
            id=str(chunk_id),
            document_id=str(document_id),
            chunking_strategy="sentence",
            start=0,
            end=100,
            text="Sample chunk text",
            status="completed",
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Mock chunk repository
        mock_chunk_repo = AsyncMock()
        mock_chunk_repo.get_by_id = AsyncMock(return_value=mock_chunk)

        mock_container = MagicMock()
        mock_container.get_chunk_read_repository = MagicMock(return_value=mock_chunk_repo)
        mock_get_container.return_value = mock_container

        # Act
        result = await enrich_search_results_activity(raw_results)

        # Assert
        assert len(result) == 1
        assert result[0]["chunk_id"] == str(chunk_id)
        assert result[0]["embedding_id"] == embedding_id
        assert result[0]["document_id"] == str(document_id)
        assert result[0]["start_index"] == 0
        assert result[0]["end_index"] == 100
        assert result[0]["score"] == 0.95
        assert result[0]["text"] == "Sample chunk text"
        assert result[0]["status"] == "completed"

    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_skips_missing_chunks(self, mock_get_container: MagicMock) -> None:
        """Test that activity skips results where chunk is not found."""
        # Arrange
        from datetime import UTC, datetime

        chunk_id_str_1 = str(uuid4())
        chunk_id_str_2 = str(uuid4())
        chunk_id_1 = ChunkId(chunk_id_str_1)
        chunk_id_2 = ChunkId(chunk_id_str_2)

        raw_results = [
            {
                "embedding_id": str(uuid4()),
                "chunk_id": chunk_id_str_1,
                "score": 0.95,
            },
            {
                "embedding_id": str(uuid4()),
                "chunk_id": chunk_id_str_2,
                "score": 0.90,
            },
        ]

        # Mock chunk repository - first chunk not found, second found
        mock_chunk = ChunkReadModel(
            id=chunk_id_str_2,
            document_id=str(uuid4()),
            chunking_strategy="sentence",
            start=0,
            end=50,
            text="Sample text",
            status="completed",
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async def mock_get_by_id(chunk_id: ChunkId) -> Any:
            if chunk_id == chunk_id_2:
                return mock_chunk
            return None

        mock_chunk_repo = AsyncMock()
        mock_chunk_repo.get_by_id = AsyncMock(side_effect=mock_get_by_id)

        mock_container = MagicMock()
        mock_container.get_chunk_read_repository = MagicMock(return_value=mock_chunk_repo)
        mock_get_container.return_value = mock_container

        # Act
        result = await enrich_search_results_activity(raw_results)

        # Assert - only second chunk should be in results
        assert len(result) == 1
        assert result[0]["chunk_id"] == chunk_id_str_2

    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_handles_empty_raw_results(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity handles empty raw results gracefully."""
        # Arrange
        raw_results: list[dict[str, Any]] = []

        mock_container = MagicMock()
        mock_chunk_repo = AsyncMock()
        mock_container.get_chunk_read_repository = MagicMock(return_value=mock_chunk_repo)
        mock_get_container.return_value = mock_container

        # Act
        result = await enrich_search_results_activity(raw_results)

        # Assert
        assert result == []
        mock_chunk_repo.get_by_id.assert_not_called()

    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_enriches_multiple_results(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity enriches multiple search results."""
        # Arrange
        from datetime import UTC, datetime

        chunk_id_strs = [str(uuid4()) for _ in range(3)]
        chunk_ids = [ChunkId(cid) for cid in chunk_id_strs]
        document_ids = [uuid4() for _ in range(3)]
        embedding_ids = [str(uuid4()) for _ in range(3)]

        raw_results = [
            {
                "embedding_id": embedding_ids[i],
                "chunk_id": chunk_id_strs[i],
                "score": 0.95 - (i * 0.05),
            }
            for i in range(3)
        ]

        # Create mock chunks
        async def mock_get_by_id(chunk_id: ChunkId) -> Any:
            idx = chunk_ids.index(chunk_id)
            return ChunkReadModel(
                id=chunk_id_strs[idx],  # Use string directly, not str(ChunkId)
                document_id=str(document_ids[idx]),
                chunking_strategy="sentence",
                start=idx * 100,
                end=(idx + 1) * 100,
                text=f"Sample text {idx}",
                status="completed",
                metadata={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        mock_chunk_repo = AsyncMock()
        mock_chunk_repo.get_by_id = AsyncMock(side_effect=mock_get_by_id)

        mock_container = MagicMock()
        mock_container.get_chunk_read_repository = MagicMock(return_value=mock_chunk_repo)
        mock_get_container.return_value = mock_container

        # Act
        result = await enrich_search_results_activity(raw_results)

        # Assert
        assert len(result) == 3
        # Verify chunks were enriched in order
        for i in range(3):
            assert result[i]["chunk_id"] == chunk_id_strs[i]
            assert result[i]["embedding_id"] == embedding_ids[i]
            assert result[i]["document_id"] == str(document_ids[i])
            assert result[i]["start_index"] == i * 100
            assert result[i]["end_index"] == (i + 1) * 100
            assert result[i]["text"] == f"Sample text {i}"

    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_enriches_results_with_document_titles(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity enriches search results with document titles."""
        # Arrange
        from datetime import UTC, datetime
        from vdb_core.application.read_models import DocumentReadModel
        from vdb_core.domain.value_objects import DocumentId

        chunk_id_1 = ChunkId(str(uuid4()))
        chunk_id_2 = ChunkId(str(uuid4()))
        document_id_1 = uuid4()
        document_id_2 = uuid4()

        raw_results = [
            {
                "embedding_id": str(uuid4()),
                "chunk_id": chunk_id_1.value,  # Use .value to get the string
                "score": 0.95,
            },
            {
                "embedding_id": str(uuid4()),
                "chunk_id": chunk_id_2.value,  # Use .value to get the string
                "score": 0.90,
            },
        ]

        # Mock chunks from two different documents
        mock_chunk_1 = ChunkReadModel(
            id=chunk_id_1.value,
            document_id=str(document_id_1),
            chunking_strategy="sentence",
            text="Sample chunk 1",
            status="completed",
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_chunk_2 = ChunkReadModel(
            id=chunk_id_2.value,
            document_id=str(document_id_2),
            chunking_strategy="sentence",
            text="Sample chunk 2",
            status="completed",
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Mock documents with titles
        mock_document_1 = DocumentReadModel(
            id=str(document_id_1),
            library_id=str(uuid4()),
            name="Bicycle",
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            upload_complete=True,
        )

        mock_document_2 = DocumentReadModel(
            id=str(document_id_2),
            library_id=str(uuid4()),
            name="Python Programming",
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            upload_complete=True,
        )

        # Mock repositories
        async def mock_get_chunk_by_id(chunk_id: ChunkId) -> Any:
            if chunk_id == chunk_id_1:
                return mock_chunk_1
            if chunk_id == chunk_id_2:
                return mock_chunk_2
            return None

        async def mock_get_document_by_id(document_id: DocumentId) -> Any:
            if str(document_id) == str(document_id_1):
                return mock_document_1
            if str(document_id) == str(document_id_2):
                return mock_document_2
            return None

        mock_chunk_repo = AsyncMock()
        mock_chunk_repo.get_by_id = AsyncMock(side_effect=mock_get_chunk_by_id)

        mock_document_repo = AsyncMock()
        mock_document_repo.get_by_id = AsyncMock(side_effect=mock_get_document_by_id)

        mock_container = MagicMock()
        mock_container.get_chunk_read_repository = MagicMock(return_value=mock_chunk_repo)
        mock_container.get_document_read_repository = MagicMock(return_value=mock_document_repo)
        mock_get_container.return_value = mock_container

        # Act
        result = await enrich_search_results_activity(raw_results)

        # Assert
        assert len(result) == 2

        # Verify first result has document title
        assert result[0]["chunk_id"] == chunk_id_1.value
        assert result[0]["document_id"] == str(document_id_1)
        assert result[0]["document_title"] == "Bicycle"
        assert result[0]["text"] == "Sample chunk 1"

        # Verify second result has document title
        assert result[1]["chunk_id"] == chunk_id_2.value
        assert result[1]["document_id"] == str(document_id_2)
        assert result[1]["document_title"] == "Python Programming"
        assert result[1]["text"] == "Sample chunk 2"

        # Verify document repository was called for each unique document
        assert mock_document_repo.get_by_id.call_count == 2

    @patch("vdb_core.infrastructure.activities.search_activities.get_di_container")
    async def test_caches_document_titles_for_same_document(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity caches document titles to avoid repeated fetches."""
        # Arrange
        from datetime import UTC, datetime
        from vdb_core.application.read_models import DocumentReadModel
        from vdb_core.domain.value_objects import DocumentId

        # Three chunks from the same document
        chunk_id_1 = ChunkId(str(uuid4()))
        chunk_id_2 = ChunkId(str(uuid4()))
        chunk_id_3 = ChunkId(str(uuid4()))
        document_id = uuid4()

        raw_results = [
            {"embedding_id": str(uuid4()), "chunk_id": str(chunk_id_1), "score": 0.95},
            {"embedding_id": str(uuid4()), "chunk_id": str(chunk_id_2), "score": 0.90},
            {"embedding_id": str(uuid4()), "chunk_id": str(chunk_id_3), "score": 0.85},
        ]

        # Mock chunks all from same document
        async def mock_get_chunk_by_id(chunk_id: ChunkId) -> Any:
            return ChunkReadModel(
                id=str(chunk_id),
                document_id=str(document_id),
                chunking_strategy="sentence",
                text="Sample text",
                status="completed",
                metadata={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        mock_document = DocumentReadModel(
            id=str(document_id),
            library_id=str(uuid4()),
            name="Bicycle Wikipedia",
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            upload_complete=True,
        )

        mock_chunk_repo = AsyncMock()
        mock_chunk_repo.get_by_id = AsyncMock(side_effect=mock_get_chunk_by_id)

        mock_document_repo = AsyncMock()
        mock_document_repo.get_by_id = AsyncMock(return_value=mock_document)

        mock_container = MagicMock()
        mock_container.get_chunk_read_repository = MagicMock(return_value=mock_chunk_repo)
        mock_container.get_document_read_repository = MagicMock(return_value=mock_document_repo)
        mock_get_container.return_value = mock_container

        # Act
        result = await enrich_search_results_activity(raw_results)

        # Assert
        assert len(result) == 3

        # All results should have same document title
        for r in result:
            assert r["document_title"] == "Bicycle Wikipedia"
            assert r["document_id"] == str(document_id)

        # Document should only be fetched once (cached for subsequent chunks)
        assert mock_document_repo.get_by_id.call_count == 1
