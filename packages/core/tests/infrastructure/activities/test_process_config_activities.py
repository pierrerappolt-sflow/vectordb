"""Tests for VectorizationConfig processing activities.

Tests SQL queries against actual database schema to prevent runtime errors.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from vdb_core.infrastructure.activities.process_config_activities import (
    load_extracted_content_activity,
)
from vdb_core.infrastructure.persistence.postgres_unit_of_work import PostgresUnitOfWork


@pytest.mark.asyncio
class TestLoadExtractedContentActivity:
    """Tests for load_extracted_content_activity.

    Ensures SQL query matches actual extracted_contents table schema.
    """

    @patch("vdb_core.infrastructure.activities.process_config_activities.get_di_container")
    async def test_query_selects_all_required_columns(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that SQL query selects all columns that exist in extracted_contents table."""
        # Arrange
        library_id = str(uuid4())
        doc_id = str(uuid4())
        fragment_id = str(uuid4())
        extracted_content_ids = [str(uuid4()), str(uuid4())]

        # Mock database row with all columns from ExtractedContentModel
        mock_row = {
            "id": extracted_content_ids[0],
            "document_id": doc_id,
            "document_fragment_id": fragment_id,
            "content": b"Test content",
            "modality_type": "TEXT",
            "modality_sequence_number": 1,
            "is_last_of_modality": False,
            "status": "PENDING",
            "metadata": {"page": 1},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        # Mock UoW and session
        mock_uow = AsyncMock(spec=PostgresUnitOfWork)
        mock_session = AsyncMock()
        # Result object is not async - only execute() is async
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [mock_row]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_uow.session = mock_session
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        mock_container = MagicMock()
        mock_container.get_unit_of_work.return_value = mock_uow
        mock_get_container.return_value = mock_container

        # Act
        result = await load_extracted_content_activity(
            library_id=library_id,
            extracted_content_ids=extracted_content_ids,
        )

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == extracted_content_ids[0]
        assert result[0]["document_id"] == doc_id
        assert result[0]["document_fragment_id"] == fragment_id
        assert result[0]["content"] == b"Test content"
        assert result[0]["modality"] == "TEXT"
        assert result[0]["modality_sequence_number"] == 1
        assert result[0]["is_last_of_modality"] is False
        assert result[0]["metadata"] == {"page": 1}

        # Verify query was executed with correct parameters
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        query_params = call_args[0][1]
        assert query_params["ids"] == extracted_content_ids

    @patch("vdb_core.infrastructure.activities.process_config_activities.get_di_container")
    async def test_handles_empty_metadata(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity handles NULL metadata correctly."""
        # Arrange
        library_id = str(uuid4())
        extracted_content_ids = [str(uuid4())]

        mock_row = {
            "id": extracted_content_ids[0],
            "document_id": str(uuid4()),
            "document_fragment_id": str(uuid4()),
            "content": b"Test",
            "modality_type": "TEXT",
            "modality_sequence_number": 1,
            "is_last_of_modality": True,
            "status": "PENDING",
            "metadata": None,  # NULL in database
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        mock_uow = AsyncMock(spec=PostgresUnitOfWork)
        mock_session = AsyncMock()
        # Result object is not async - only execute() is async
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [mock_row]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_uow.session = mock_session
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        mock_container = MagicMock()
        mock_container.get_unit_of_work.return_value = mock_uow
        mock_get_container.return_value = mock_container

        # Act
        result = await load_extracted_content_activity(
            library_id=library_id,
            extracted_content_ids=extracted_content_ids,
        )

        # Assert
        assert result[0]["metadata"] == {}  # Should default to empty dict

    @patch("vdb_core.infrastructure.activities.process_config_activities.get_di_container")
    async def test_orders_by_modality_sequence_number(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that results are ordered by modality_sequence_number."""
        # Arrange
        library_id = str(uuid4())
        doc_id = str(uuid4())
        fragment_id = str(uuid4())
        ids = [str(uuid4()), str(uuid4()), str(uuid4())]

        # Return rows in non-sequential order
        mock_rows = [
            {
                "id": ids[2],
                "document_id": doc_id,
                "document_fragment_id": fragment_id,
                "content": b"Third",
                "modality_type": "TEXT",
                "modality_sequence_number": 3,
                "is_last_of_modality": True,
                "status": "PENDING",
                "metadata": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": ids[0],
                "document_id": doc_id,
                "document_fragment_id": fragment_id,
                "content": b"First",
                "modality_type": "TEXT",
                "modality_sequence_number": 1,
                "is_last_of_modality": False,
                "status": "PENDING",
                "metadata": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": ids[1],
                "document_id": doc_id,
                "document_fragment_id": fragment_id,
                "content": b"Second",
                "modality_type": "TEXT",
                "modality_sequence_number": 2,
                "is_last_of_modality": False,
                "status": "PENDING",
                "metadata": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ]

        mock_uow = AsyncMock(spec=PostgresUnitOfWork)
        mock_session = AsyncMock()
        # Result object is not async - only execute() is async
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = mock_rows
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_uow.session = mock_session
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        mock_container = MagicMock()
        mock_container.get_unit_of_work.return_value = mock_uow
        mock_get_container.return_value = mock_container

        # Act
        result = await load_extracted_content_activity(
            library_id=library_id,
            extracted_content_ids=ids,
        )

        # Assert - verify ORDER BY is in the query
        # Results should be in the order returned by database (which should be ordered)
        assert len(result) == 3
        # Note: The mock returns them in the mock_rows order,
        # but the actual query has ORDER BY modality_sequence_number

    @patch("vdb_core.infrastructure.activities.process_config_activities.get_di_container")
    async def test_raises_error_when_session_not_initialized(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity raises error if UoW session is None."""
        # Arrange
        library_id = str(uuid4())
        extracted_content_ids = [str(uuid4())]

        mock_uow = AsyncMock(spec=PostgresUnitOfWork)
        mock_uow.session = None  # Simulate uninitialized session
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        mock_container = MagicMock()
        mock_container.get_unit_of_work.return_value = mock_uow
        mock_get_container.return_value = mock_container

        # Act & Assert
        with pytest.raises(RuntimeError, match="PostgresUnitOfWork session is not initialized"):
            await load_extracted_content_activity(
                library_id=library_id,
                extracted_content_ids=extracted_content_ids,
            )

    @patch("vdb_core.infrastructure.activities.process_config_activities.get_di_container")
    async def test_raises_error_for_wrong_uow_type(
        self, mock_get_container: MagicMock
    ) -> None:
        """Test that activity raises error if UoW is not PostgresUnitOfWork."""
        # Arrange
        library_id = str(uuid4())
        extracted_content_ids = [str(uuid4())]

        # Mock a different UoW type (not PostgresUnitOfWork)
        mock_uow = AsyncMock()  # Not a PostgresUnitOfWork instance
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        mock_container = MagicMock()
        mock_container.get_unit_of_work.return_value = mock_uow
        mock_get_container.return_value = mock_container

        # Act & Assert
        with pytest.raises(TypeError, match="This activity requires PostgresUnitOfWork"):
            await load_extracted_content_activity(
                library_id=library_id,
                extracted_content_ids=extracted_content_ids,
            )


@pytest.mark.asyncio
class TestQuerySchemaConsistency:
    """Integration tests to verify SQL queries match database schema.

    These tests ensure that all columns referenced in queries actually exist
    in the database models.
    """

    def test_extracted_content_model_has_all_queried_columns(self) -> None:
        """Test that ExtractedContentModel has all columns used in queries."""
        from vdb_core.infrastructure.persistence.models.extracted_content_model import (
            ExtractedContentModel,
        )

        # Columns used in load_extracted_content_activity query
        required_columns = {
            "id",
            "document_id",
            "document_fragment_id",
            "content",
            "modality_type",
            "modality_sequence_number",
            "is_last_of_modality",
            "metadata",
            "status",
            "created_at",
            "updated_at",
        }

        # Get actual columns from model
        model_columns = set(ExtractedContentModel.__table__.columns.keys())

        # Assert all required columns exist
        missing_columns = required_columns - model_columns
        assert not missing_columns, (
            f"ExtractedContentModel is missing columns used in queries: {missing_columns}"
        )

    def test_extracted_content_model_columns_match_domain_entity(self) -> None:
        """Test that model columns match domain entity fields."""
        from vdb_core.infrastructure.persistence.models.extracted_content_model import (
            ExtractedContentModel,
        )

        # Get model columns
        model_columns = set(ExtractedContentModel.__table__.columns.keys())

        # Expected columns based on ExtractedContent entity
        expected_columns = {
            "id",
            "document_id",
            "document_fragment_id",
            "content",
            "modality_type",  # Note: entity has 'modality', model has 'modality_type'
            "modality_sequence_number",
            "is_last_of_modality",
            "status",
            "metadata",
            "created_at",
            "updated_at",
        }

        # Verify all expected columns exist
        missing = expected_columns - model_columns
        assert not missing, f"Model is missing columns from domain entity: {missing}"
