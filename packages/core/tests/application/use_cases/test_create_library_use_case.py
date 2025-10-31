"""Tests for CreateLibraryCommand."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from vdb_core.application.commands import CreateLibraryCommand, CreateLibraryInput
from vdb_core.domain.events import LibraryCreated
from vdb_core.domain.value_objects import LibraryId


@pytest.mark.asyncio
async def test_create_library_command_success(mock_uow: MagicMock, mock_event_bus: AsyncMock) -> None:
    """Test successful library creation."""
    # Arrange - configure mock UoW
    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.add = AsyncMock()

    mock_event = MagicMock(spec=LibraryCreated)
    mock_uow.commit = AsyncMock(return_value=[mock_event])

    # Mock config read repository that returns empty list
    mock_config_read_repo = AsyncMock()
    mock_config_read_repo.get_all = AsyncMock(return_value=[])

    # Act
    command = CreateLibraryCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
        config_read_repo_factory=lambda: mock_config_read_repo,
    )
    input_data = CreateLibraryInput(name="Test Library")
    library_id = await command.execute(input_data)

    # Assert
    assert isinstance(library_id, LibraryId)
    mock_uow.libraries.add.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_event_bus.handle_events.assert_called_once_with([mock_event])


@pytest.mark.asyncio
async def test_create_library_command_validation_error(mock_uow: MagicMock, mock_event_bus: AsyncMock) -> None:
    """Test that validation errors are raised."""
    from pydantic_core import ValidationError

    # Mock config read repository
    mock_config_read_repo = AsyncMock()
    mock_config_read_repo.get_all = AsyncMock(return_value=[])

    # Act & Assert
    command = CreateLibraryCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
        config_read_repo_factory=lambda: mock_config_read_repo,
    )

    with pytest.raises(ValidationError):
        # Empty name should fail validation
        input_data = CreateLibraryInput(name="")
        await command.execute(input_data)


@pytest.mark.asyncio
async def test_create_library_command_rollback_on_error(mock_uow: MagicMock, mock_event_bus: AsyncMock) -> None:
    """Test that UoW rolls back on error."""
    # Arrange - configure mock UoW
    mock_uow.libraries = AsyncMock()
    mock_uow.libraries.add = AsyncMock()
    mock_uow.commit = AsyncMock(side_effect=Exception("Database error"))

    # Mock config read repository
    mock_config_read_repo = AsyncMock()
    mock_config_read_repo.get_all = AsyncMock(return_value=[])

    # Act & Assert
    command = CreateLibraryCommand(
        uow_factory=lambda: mock_uow,
        message_bus=mock_event_bus,
        config_read_repo_factory=lambda: mock_config_read_repo,
    )
    input_data = CreateLibraryInput(name="Test Library")

    with pytest.raises(Exception, match="Database error"):
        await command.execute(input_data)

    # Verify __aexit__ was called (context manager cleanup)
    mock_uow.__aexit__.assert_called_once()

    # Verify events were NOT published
    mock_event_bus.handle_events.assert_not_called()
