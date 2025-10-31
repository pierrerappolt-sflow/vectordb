"""Tests for Document commands."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from vdb_core.application.commands import (
    CreateDocumentCommand,
    CreateDocumentFragmentCommand,
    CreateDocumentFragmentInput,
    CreateDocumentInput,
    DeleteDocumentCommand,
    DeleteDocumentInput,
    UpdateDocumentCommand,
    UpdateDocumentInput,
)
from vdb_core.domain.entities.library import Document
from vdb_core.domain.events import DocumentCreated, DocumentDeleted, DocumentUpdated
from vdb_core.domain.exceptions import LibraryNotFoundError
from vdb_core.domain.value_objects import ContentHash, DocumentId


@pytest.mark.asyncio
async def test_create_document_command_success(mock_uow: MagicMock, mock_event_bus: AsyncMock) -> None:
    """Test successful document creation."""
    # Arrange
    library_id = uuid4()
    document_id = uuid4()
    document_name = "test.pdf"

    # Mock library with add_document method
    mock_library = MagicMock()
    mock_document = MagicMock(spec=Document)
    mock_document.id = document_id  # DocumentId is just UUID
    mock_library.add_document.return_value = mock_document

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get = AsyncMock(return_value=mock_library)

    mock_event = MagicMock(spec=DocumentCreated)
    mock_uow.commit = AsyncMock(return_value=[mock_event])

    # Act
    command = CreateDocumentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = CreateDocumentInput(library_id=str(library_id), name=document_name)
    document_id = await command.execute(input_data)

    # Assert
    assert isinstance(document_id, DocumentId)
    mock_uow.libraries.get.assert_called_once_with(library_id)
    mock_library.add_document.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_event_bus.handle_events.assert_called_once_with([mock_event])


@pytest.mark.asyncio
async def test_create_document_command_library_not_found(
    mock_uow: MagicMock, mock_event_bus: AsyncMock
) -> None:
    """Test that LibraryNotFoundError is raised when library doesn't exist."""
    # Arrange
    from vdb_core.domain.exceptions import EntityNotFoundError

    library_id = uuid4()

    mock_uow.libraries = AsyncMock()
    # Repository.get() now raises EntityNotFoundError instead of returning None
    mock_uow.libraries.get = AsyncMock(side_effect=EntityNotFoundError(f"Entity with id {library_id} not found"))

    # Act & Assert
    command = CreateDocumentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = CreateDocumentInput(library_id=str(library_id), name="test.pdf")

    with pytest.raises(LibraryNotFoundError):
        await command.execute(input_data)

    # Verify no commit occurred
    mock_uow.commit.assert_not_called()
    mock_event_bus.handle_events.assert_not_called()


@pytest.mark.asyncio
async def test_update_document_command_success(mock_uow: MagicMock, mock_event_bus: AsyncMock) -> None:
    """Test successful document update."""
    # Arrange
    document_id = uuid4()
    new_name = "updated.pdf"

    # Mock library with update_document method
    mock_library = MagicMock()
    mock_document = MagicMock(spec=Document)
    mock_document.id = document_id  # DocumentId is just UUID
    mock_library.update_document = AsyncMock(return_value=mock_document)

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get_by_document_id = AsyncMock(return_value=mock_library)

    mock_event = MagicMock(spec=DocumentUpdated)
    mock_uow.commit = AsyncMock(return_value=[mock_event])

    # Act
    command = UpdateDocumentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = UpdateDocumentInput(document_id=str(document_id), name=new_name)
    result_id = await command.execute(input_data)

    # Assert
    assert result_id == mock_document.id
    mock_uow.libraries.get_by_document_id.assert_called_once_with(document_id)
    mock_library.update_document.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_event_bus.handle_events.assert_called_once_with([mock_event])


@pytest.mark.asyncio
async def test_update_document_command_rollback_on_error(
    mock_uow: MagicMock, mock_event_bus: AsyncMock
) -> None:
    """Test that UoW rolls back on error during update."""
    # Arrange
    document_id = uuid4()

    mock_library = MagicMock()
    mock_library.update_document = AsyncMock()

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get_by_document_id = AsyncMock(return_value=mock_library)
    mock_uow.commit = AsyncMock(side_effect=Exception("Database error"))

    # Act & Assert
    command = UpdateDocumentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = UpdateDocumentInput(document_id=str(document_id), name="updated.pdf")

    with pytest.raises(Exception, match="Database error"):
        await command.execute(input_data)

    # Verify __aexit__ was called (context manager cleanup)
    mock_uow.__aexit__.assert_called_once()

    # Verify events were NOT published
    mock_event_bus.handle_events.assert_not_called()


@pytest.mark.asyncio
async def test_delete_document_command_success(mock_uow: MagicMock, mock_event_bus: AsyncMock) -> None:
    """Test successful document deletion."""
    # Arrange
    document_id = uuid4()

    # Mock library with remove_document method
    mock_library = MagicMock()
    mock_library.remove_document = AsyncMock()

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get_by_document_id = AsyncMock(return_value=mock_library)

    mock_event = MagicMock(spec=DocumentDeleted)
    mock_uow.commit = AsyncMock(return_value=[mock_event])

    # Act
    command = DeleteDocumentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = DeleteDocumentInput(document_id=str(document_id))
    result = await command.execute(input_data)

    # Assert
    assert result is None
    mock_uow.libraries.get_by_document_id.assert_called_once_with(document_id)
    mock_library.remove_document.assert_called_once_with(document_id)
    mock_uow.commit.assert_called_once()
    mock_event_bus.handle_events.assert_called_once_with([mock_event])


@pytest.mark.asyncio
async def test_delete_document_command_rollback_on_error(
    mock_uow: MagicMock, mock_event_bus: AsyncMock
) -> None:
    """Test that UoW rolls back on error during deletion."""
    # Arrange
    document_id = uuid4()

    mock_library = MagicMock()
    mock_library.remove_document = AsyncMock()

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get_by_document_id = AsyncMock(return_value=mock_library)
    mock_uow.commit = AsyncMock(side_effect=Exception("Database error"))

    # Act & Assert
    command = DeleteDocumentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = DeleteDocumentInput(document_id=str(document_id))

    with pytest.raises(Exception, match="Database error"):
        await command.execute(input_data)

    # Verify __aexit__ was called (context manager cleanup)
    mock_uow.__aexit__.assert_called_once()

    # Verify events were NOT published
    mock_event_bus.handle_events.assert_not_called()


@pytest.mark.asyncio
async def test_create_document_fragment_command_success(
    mock_uow: MagicMock, mock_event_bus: AsyncMock
) -> None:
    """Test successful document fragment creation."""
    # Arrange
    library_id = uuid4()
    document_id = uuid4()
    fragment_content = b"test content"

    # Mock library with add_document_fragment method
    mock_library = MagicMock()
    mock_fragment = MagicMock()
    mock_fragment.id = uuid4()
    mock_library.add_document_fragment = AsyncMock(return_value=mock_fragment)

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get = AsyncMock(return_value=mock_library)

    mock_event = MagicMock()
    mock_uow.commit = AsyncMock(return_value=[mock_event])

    # Act
    command = CreateDocumentFragmentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = CreateDocumentFragmentInput(
        library_id=str(library_id),
        document_id=str(document_id),
        sequence_number=0,
        content=fragment_content,
        is_final=False,
    )
    fragment_id = await command.execute(input_data)

    # Assert
    assert fragment_id == str(mock_fragment.id)
    mock_uow.libraries.get.assert_called_once_with(library_id)
    mock_library.add_document_fragment.assert_called_once()

    # Verify content hash was created correctly
    call_args = mock_library.add_document_fragment.call_args
    assert call_args is not None
    assert call_args[1]["content"] == fragment_content
    assert isinstance(call_args[1]["content_hash"], ContentHash)
    assert call_args[1]["is_final"] is False

    mock_uow.commit.assert_called_once()
    mock_event_bus.handle_events.assert_called_once_with([mock_event])


@pytest.mark.asyncio
async def test_create_document_fragment_command_library_not_found(
    mock_uow: MagicMock, mock_event_bus: AsyncMock
) -> None:
    """Test that LibraryNotFoundError is raised when library doesn't exist."""
    # Arrange
    library_id = uuid4()
    document_id = uuid4()

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get = AsyncMock(return_value=None)

    # Act & Assert
    command = CreateDocumentFragmentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = CreateDocumentFragmentInput(
        library_id=str(library_id),
        document_id=str(document_id),
        sequence_number=0,
        content=b"test",
        is_final=False,
    )

    with pytest.raises(LibraryNotFoundError):
        await command.execute(input_data)

    # Verify no commit occurred
    mock_uow.commit.assert_not_called()
    mock_event_bus.handle_events.assert_not_called()


@pytest.mark.asyncio
async def test_create_document_fragment_command_final_fragment(
    mock_uow: MagicMock, mock_event_bus: AsyncMock
) -> None:
    """Test creating final fragment with is_final=True."""
    # Arrange
    library_id = uuid4()
    document_id = uuid4()

    mock_library = MagicMock()
    mock_fragment = MagicMock()
    mock_fragment.id = uuid4()
    mock_library.add_document_fragment = AsyncMock(return_value=mock_fragment)

    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.get = AsyncMock(return_value=mock_library)
    mock_uow.commit = AsyncMock(return_value=[])

    # Act
    command = CreateDocumentFragmentCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
    )
    input_data = CreateDocumentFragmentInput(
        library_id=str(library_id),
        document_id=str(document_id),
        sequence_number=5,
        content=b"final content",
        is_final=True,
    )
    await command.execute(input_data)

    # Assert
    call_args = mock_library.add_document_fragment.call_args
    assert call_args is not None
    assert call_args[1]["is_final"] is True
    assert call_args[1]["sequence_number"] == 5
