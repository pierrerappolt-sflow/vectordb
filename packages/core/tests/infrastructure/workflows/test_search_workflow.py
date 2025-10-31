"""Integration tests for SearchWorkflow - vector similarity search orchestration."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from vdb_core.infrastructure.workflows.search_workflow import (
    SearchWorkflow,
    SearchWorkflowInput,
    SearchWorkflowResult,
)


@pytest.mark.asyncio
class TestSearchWorkflow:
    """Integration tests for SearchWorkflow orchestration."""

    @patch("vdb_core.infrastructure.workflows.search_workflow.workflow")
    async def test_workflow_executes_all_three_activities_in_sequence(
        self, mock_workflow: MagicMock
    ) -> None:
        """Test that workflow executes all activities in correct order."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_text = "test query"
        top_k = 5
        strategy = "test-strategy"

        # Track activity execution order
        activity_calls: list[str] = []

        async def mock_activity_execution(activity_fn, **kwargs):  # type: ignore
            activity_name = activity_fn.__name__
            activity_calls.append(activity_name)

            if activity_name == "generate_query_embedding_activity":
                return [0.1] * 1024  # Return embedding vector
            if activity_name == "search_vectors_activity":
                return [
                    {
                        "embedding_id": str(uuid4()),
                        "chunk_id": str(uuid4()),
                        "score": 0.95,
                    }
                ]
            if activity_name == "enrich_search_results_activity":
                return [
                    {
                        "chunk_id": str(uuid4()),
                        "embedding_id": str(uuid4()),
                        "document_id": str(uuid4()),
                        "start_index": 0,
                        "end_index": 100,
                        "score": 0.95,
                        "status": "COMPLETED",
                    }
                ]
            return []

        mock_workflow.execute_activity = AsyncMock(side_effect=mock_activity_execution)
        mock_workflow.logger = MagicMock()

        # Create workflow instance
        workflow_instance = SearchWorkflow()

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text=query_text,
            top_k=top_k,
            strategy=strategy,
        )
        result = await workflow_instance.run(input_data)

        # Assert - verify all activities executed in correct order
        assert len(activity_calls) == 5
        assert activity_calls[0] == "update_query_status_activity"  # Set to PROCESSING
        assert activity_calls[1] == "generate_query_embedding_activity"
        assert activity_calls[2] == "search_vectors_activity"
        assert activity_calls[3] == "enrich_search_results_activity"
        assert activity_calls[4] == "update_query_status_activity"  # Set to COMPLETED

        # Verify result structure
        assert isinstance(result, SearchWorkflowResult)
        assert result.query_text == query_text
        assert result.result_count == 1
        assert len(result.results) == 1

    @patch("vdb_core.infrastructure.workflows.search_workflow.workflow")
    async def test_workflow_passes_correct_args_to_generate_embedding(
        self, mock_workflow: MagicMock
    ) -> None:
        """Test that workflow passes correct arguments to embedding activity."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_text = "what is machine learning?"
        strategy = "cohere-v3"

        mock_workflow.execute_activity = AsyncMock(
            side_effect=[
                None,  # Update status to PROCESSING
                [0.1] * 1024,  # Embedding activity
                [],  # Search activity
                [],  # Enrich activity
                None,  # Update status to COMPLETED
            ]
        )
        mock_workflow.logger = MagicMock()

        workflow_instance = SearchWorkflow()

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text=query_text,
            top_k=10,
            strategy=strategy,
        )
        await workflow_instance.run(input_data)

        # Assert - check second activity call (generate_query_embedding, first is update_status)
        second_call = mock_workflow.execute_activity.call_args_list[1]
        assert second_call[1]["args"] == [query_text, library_id, strategy]

    @patch("vdb_core.infrastructure.workflows.search_workflow.workflow")
    async def test_workflow_passes_correct_args_to_search_vectors(
        self, mock_workflow: MagicMock
    ) -> None:
        """Test that workflow passes embedding result to search activity."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_vector = [0.2] * 1024
        top_k = 3

        mock_workflow.execute_activity = AsyncMock(
            side_effect=[
                None,  # Update status to PROCESSING
                query_vector,  # Embedding activity returns this vector
                [],  # Search activity
                [],  # Enrich activity
                None,  # Update status to COMPLETED
            ]
        )
        mock_workflow.logger = MagicMock()

        workflow_instance = SearchWorkflow()

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text="test",
            top_k=top_k,
            strategy="test-strategy",
        )
        await workflow_instance.run(input_data)

        # Assert - check third activity call (search_vectors, first is update_status, second is embedding)
        third_call = mock_workflow.execute_activity.call_args_list[2]
        assert third_call[1]["args"] == [library_id, config_id, query_vector, top_k]

    @patch("vdb_core.infrastructure.workflows.search_workflow.workflow")
    async def test_workflow_passes_correct_args_to_enrich_results(
        self, mock_workflow: MagicMock
    ) -> None:
        """Test that workflow passes search results to enrich activity."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        raw_results = [
            {"embedding_id": str(uuid4()), "chunk_id": str(uuid4()), "score": 0.95},
            {"embedding_id": str(uuid4()), "chunk_id": str(uuid4()), "score": 0.88},
        ]

        enriched_results = [
            {**r, "document_id": str(uuid4()), "start_index": 0, "end_index": 100, "status": "completed", "text": "text"}
            for r in raw_results
        ]

        mock_workflow.execute_activity = AsyncMock(
            side_effect=[
                None,  # Update status to PROCESSING
                [0.1] * 1024,  # Embedding activity
                raw_results,  # Search activity returns these results
                enriched_results,  # Enrich activity
                None,  # Update status to COMPLETED
            ]
        )
        mock_workflow.logger = MagicMock()

        workflow_instance = SearchWorkflow()

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text="test",
            top_k=10,
            strategy="test-strategy",
        )
        await workflow_instance.run(input_data)

        # Assert - check fourth activity call (enrich_search_results, after update_status, embedding, search)
        fourth_call = mock_workflow.execute_activity.call_args_list[3]
        assert fourth_call[1]["args"] == [raw_results]

    @patch("vdb_core.infrastructure.workflows.search_workflow.workflow")
    async def test_workflow_handles_empty_search_results(
        self, mock_workflow: MagicMock
    ) -> None:
        """Test that workflow handles case with no search results."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())

        # Mock activities - search returns no results
        mock_workflow.execute_activity = AsyncMock(
            side_effect=[
                None,  # Update status to PROCESSING
                [0.1] * 1024,  # Embedding activity
                [],  # Search activity - no results
                [],  # Enrich activity - no results
                None,  # Update status to COMPLETED
            ]
        )
        mock_workflow.logger = MagicMock()

        workflow_instance = SearchWorkflow()

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text="nonexistent query",
            top_k=10,
            strategy="test-strategy",
        )
        result = await workflow_instance.run(input_data)

        # Assert
        assert result.result_count == 0
        assert result.results == []
        assert result.query_text == "nonexistent query"

    @patch("vdb_core.infrastructure.workflows.search_workflow.workflow")
    async def test_workflow_returns_correct_result_structure(
        self, mock_workflow: MagicMock
    ) -> None:
        """Test that workflow returns properly structured SearchWorkflowResult."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_text = "test query"
        enriched_results = [
            {
                "chunk_id": str(uuid4()),
                "embedding_id": str(uuid4()),
                "document_id": str(uuid4()),
                "start_index": 0,
                "end_index": 100,
                "score": 0.95,
                "status": "COMPLETED",
            },
            {
                "chunk_id": str(uuid4()),
                "embedding_id": str(uuid4()),
                "document_id": str(uuid4()),
                "start_index": 100,
                "end_index": 200,
                "score": 0.87,
                "status": "COMPLETED",
            },
        ]

        mock_workflow.execute_activity = AsyncMock(
            side_effect=[
                None,  # Update status to PROCESSING
                [0.1] * 1024,  # Embedding
                [],  # Search (raw results)
                enriched_results,  # Enrich
                None,  # Update status to COMPLETED
            ]
        )
        mock_workflow.logger = MagicMock()

        workflow_instance = SearchWorkflow()

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text=query_text,
            top_k=10,
            strategy="test-strategy",
        )
        result = await workflow_instance.run(input_data)

        # Assert
        assert isinstance(result, SearchWorkflowResult)
        assert result.query_text == query_text
        assert result.result_count == 2
        assert result.results == enriched_results
        assert len(result.results) == 2

    @patch("vdb_core.infrastructure.workflows.search_workflow.workflow")
    async def test_workflow_logs_progress(self, mock_workflow: MagicMock) -> None:
        """Test that workflow logs progress at each step."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())

        mock_workflow.execute_activity = AsyncMock(
            side_effect=[
                None,  # Update status to PROCESSING
                [0.1] * 1024,  # Embedding
                [],  # Search
                [],  # Enrich
                None,  # Update status to COMPLETED
            ]
        )
        mock_logger = MagicMock()
        mock_workflow.logger = mock_logger

        workflow_instance = SearchWorkflow()

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text="test",
            top_k=10,
            strategy="test-strategy",
        )
        await workflow_instance.run(input_data)

        # Assert - verify logging calls
        assert mock_logger.info.call_count >= 4
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]

        assert any("Starting search workflow" in msg for msg in log_messages)
        assert any("Step 1" in msg or "Generating query embedding" in msg for msg in log_messages)
        assert any("Step 2" in msg or "Searching vector index" in msg for msg in log_messages)
        assert any("Step 3" in msg or "Enriching results" in msg for msg in log_messages)


class TestSearchWorkflowInput:
    """Tests for SearchWorkflowInput validation."""

    def test_input_requires_all_fields(self) -> None:
        """Test that all required fields must be provided."""
        # Act & Assert
        with pytest.raises(TypeError):
            SearchWorkflowInput()  # type: ignore

    def test_input_accepts_valid_data(self) -> None:
        """Test that input accepts valid data."""
        # Arrange
        library_id = str(uuid4())
        config_id = str(uuid4())
        query_text = "test query"
        top_k = 5
        strategy = "test-strategy"

        # Act
        input_data = SearchWorkflowInput(
            query_id=str(uuid4()),
            library_id=library_id,
            config_id=config_id,
            query_text=query_text,
            top_k=top_k,
            strategy=strategy,
        )

        # Assert
        assert input_data.library_id == library_id
        assert input_data.config_id == config_id
        assert input_data.query_text == query_text
        assert input_data.top_k == top_k
        assert input_data.strategy == strategy

    def test_input_supports_various_top_k_values(self) -> None:
        """Test that input supports different top_k values."""
        # Arrange & Act
        for k in [1, 5, 10, 50, 100]:
            input_data = SearchWorkflowInput(
                query_id=str(uuid4()),
                library_id=str(uuid4()),
                config_id=str(uuid4()),
                query_text="test",
                top_k=k,
                strategy="test-strategy",
            )
            # Assert
            assert input_data.top_k == k


class TestSearchWorkflowResult:
    """Tests for SearchWorkflowResult structure."""

    def test_result_structure(self) -> None:
        """Test that result has correct structure."""
        # Arrange
        results = [
            {
                "chunk_id": str(uuid4()),
                "document_id": str(uuid4()),
                "start_index": 0,
                "end_index": 100,
                "score": 0.95,
                "status": "COMPLETED",
            }
        ]
        query_text = "test query"

        # Act
        result = SearchWorkflowResult(
            results=results,
            query_text=query_text,
            result_count=len(results),
        )

        # Assert
        assert result.results == results
        assert result.query_text == query_text
        assert result.result_count == 1

    def test_result_handles_empty_results(self) -> None:
        """Test that result can represent empty search results."""
        # Act
        result = SearchWorkflowResult(
            results=[],
            query_text="nonexistent",
            result_count=0,
        )

        # Assert
        assert result.results == []
        assert result.result_count == 0
        assert result.query_text == "nonexistent"
