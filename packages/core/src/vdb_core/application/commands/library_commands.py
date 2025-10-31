"""Library commands for write operations.

Following the Command pattern with Command[TInput, TOutput] base class.
Each command encapsulates the business logic for a specific write operation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from vdb_core.application.base.command import Command
from vdb_core.application.commands.inputs import (
    AddConfigToLibraryInput,
    CreateLibraryInput,
    DeleteLibraryInput,
    RemoveConfigFromLibraryInput,
    UpdateLibraryInput,
)
from vdb_core.domain.entities import Library
from vdb_core.domain.exceptions import LibraryNotFoundError
from vdb_core.domain.value_objects import (
    LibraryId,
    LibraryName,
    LibraryStatus,
    VectorizationConfigId,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.message_bus import IMessageBus
    from vdb_core.application.repositories import IVectorizationConfigReadRepository


class CreateLibraryCommand(Command[CreateLibraryInput, LibraryId]):
    """Command to create a new library and associate all existing vectorization configs.

    Automatically associates ALL vectorization configs in the database
    with the newly created library (regardless of status).

    Example:
        command = CreateLibraryCommand(uow_factory, message_bus, config_read_repo_factory)
        library_id = await command.execute(
            CreateLibraryInput(name="My Library")
        )

    """

    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
        message_bus: IMessageBus,
        config_read_repo_factory: Callable[[], IVectorizationConfigReadRepository],
    ) -> None:
        """Initialize command with dependencies.

        Args:
            uow_factory: Factory function that creates UoW instances
            message_bus: Message bus for routing events to handlers
            config_read_repo_factory: Factory for vectorization config read repository

        """
        super().__init__(uow_factory, message_bus)
        self.config_read_repo_factory = config_read_repo_factory

    async def _execute(self, input_data: CreateLibraryInput, uow: IUnitOfWork) -> LibraryId:
        """Create a new library and associate all vectorization configs.

        Args:
            input_data: The create library input data
            uow: Active Unit of Work (within transaction)

        Returns:
            The newly created library's ID

        """
        # Create the library
        library = Library(name=LibraryName(value=input_data.name))
        await uow.libraries.add(library)

        # Get all vectorization configs from read repository (regardless of status)
        config_read_repo = self.config_read_repo_factory()
        all_configs = await config_read_repo.get_all(statuses=None)

        # Associate each config with the library
        for config_read_model in all_configs:
            config_id = VectorizationConfigId(UUID(config_read_model.id))
            library.add_config(config_id)

        return library.id

class UpdateLibraryCommand(Command[UpdateLibraryInput, LibraryId]):
    """Command to update an existing library.

    Example:
        command = UpdateLibraryCommand(uow_factory, message_bus)
        library_id = await command.execute(
            UpdateLibraryInput(library_id="uuid", name="New Name")
        )

    """

    async def _execute(self, input_data: UpdateLibraryInput, uow: IUnitOfWork) -> LibraryId:
        """Update an existing library.

        Args:
            input_data: The update library input data
            uow: Active Unit of Work (within transaction)

        Returns:
            The updated library's ID

        """
        library_id_vo = LibraryId(input_data.library_id)

        # Load library (raises LibraryNotFoundError if not found)
        library = await uow.libraries.get(library_id_vo)
        if library is None:
            msg = f"Library {library_id_vo} not found"
            raise LibraryNotFoundError(msg)

        # Update library name using update() method
        library.update(name=LibraryName(value=input_data.name))

        return library.id

class DeleteLibraryCommand(Command[DeleteLibraryInput, None]):
    """Command to soft-delete a library.

    Sets the library status to DELETED instead of removing from database.
    Deleted libraries are filtered out from queries but remain in the database.

    Example:
        command = DeleteLibraryCommand(uow_factory, message_bus)
        await command.execute(DeleteLibraryInput(library_id="uuid"))

    """

    async def _execute(self, input_data: DeleteLibraryInput, uow: IUnitOfWork) -> None:
        """Soft-delete a library by marking status as DELETED.

        Args:
            input_data: The delete library input data
            uow: Active Unit of Work (within transaction)

        """
        library_id_vo = LibraryId(input_data.library_id)

        # Load library (raises LibraryNotFoundError if not found)
        library = await uow.libraries.get(library_id_vo)
        if library is None:
            msg = f"Library {library_id_vo} not found"
            raise LibraryNotFoundError(msg)

        # Soft delete: update status to DELETED
        library.update(status=LibraryStatus.DELETED)


class AddConfigToLibraryCommand(Command[AddConfigToLibraryInput, None]):
    """Command to associate a vectorization config with a library.

    Following Cosmic Python pattern:
    - Loads library aggregate
    - Calls library.add_config() which raises LibraryConfigAdded event
    - Event handler will trigger processing of all library documents with this config

    Example:
        command = AddConfigToLibraryCommand(uow_factory, message_bus)
        await command.execute(
            AddConfigToLibraryInput(library_id="uuid", config_id="uuid")
        )

    """

    async def _execute(self, input_data: AddConfigToLibraryInput, uow: IUnitOfWork) -> None:
        """Associate a config with a library.

        Args:
            input_data: The add config input data
            uow: Active Unit of Work (within transaction)

        Raises:
            LibraryNotFoundError: If library doesn't exist
            ValidationException: If config already associated with library

        """
        library_id_vo = LibraryId(input_data.library_id)
        config_id_vo = VectorizationConfigId(UUID(input_data.config_id))

        # Load library (raises LibraryNotFoundError if not found)
        library = await uow.libraries.get(library_id_vo)

        # Add config association (raises LibraryConfigAdded event as side effect)
        library.add_config(config_id_vo)


class RemoveConfigFromLibraryCommand(Command[RemoveConfigFromLibraryInput, None]):
    """Command to disassociate a vectorization config from a library.

    Following Cosmic Python pattern:
    - Loads library aggregate
    - Calls library.remove_config() which raises LibraryConfigRemoved event
    - Does NOT delete the config itself (configs are global)

    Example:
        command = RemoveConfigFromLibraryCommand(uow_factory, message_bus)
        await command.execute(
            RemoveConfigFromLibraryInput(library_id="uuid", config_id="uuid")
        )

    """

    async def _execute(self, input_data: RemoveConfigFromLibraryInput, uow: IUnitOfWork) -> None:
        """Disassociate a config from a library.

        Args:
            input_data: The remove config input data
            uow: Active Unit of Work (within transaction)

        Raises:
            LibraryNotFoundError: If library doesn't exist
            ValidationException: If config not associated with library

        """
        library_id_vo = LibraryId(input_data.library_id)
        config_id_vo = VectorizationConfigId(UUID(input_data.config_id))

        # Load library (raises LibraryNotFoundError if not found)
        library = await uow.libraries.get(library_id_vo)

        # Remove config association (raises LibraryConfigRemoved event as side effect)
        library.remove_config(config_id_vo)
