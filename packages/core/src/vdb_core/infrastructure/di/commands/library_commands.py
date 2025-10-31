"""Dependency injection providers for library commands."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from vdb_core.application.commands import (
    AddConfigToLibraryCommand,
    CreateLibraryCommand,
    DeleteLibraryCommand,
    RemoveConfigFromLibraryCommand,
    UpdateLibraryCommand,
)

if TYPE_CHECKING:
    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.message_bus import IMessageBus
    from vdb_core.application.repositories import IVectorizationConfigReadRepository


def provide_create_library_command(
    uow_factory: Callable[[], "IUnitOfWork"],
    message_bus: "IMessageBus",
    config_read_repo_factory: Callable[[], "IVectorizationConfigReadRepository"],
) -> CreateLibraryCommand:
    """Provide CreateLibraryCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers
        config_read_repo_factory: Factory for vectorization config read repository

    Returns:
        Configured CreateLibraryCommand instance

    """
    return CreateLibraryCommand(
        uow_factory=uow_factory, message_bus=message_bus, config_read_repo_factory=config_read_repo_factory
    )


def provide_update_library_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> UpdateLibraryCommand:
    """Provide UpdateLibraryCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured UpdateLibraryCommand instance

    """
    return UpdateLibraryCommand(uow_factory=uow_factory, message_bus=message_bus)


def provide_delete_library_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> DeleteLibraryCommand:
    """Provide DeleteLibraryCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured DeleteLibraryCommand instance

    """
    return DeleteLibraryCommand(uow_factory=uow_factory, message_bus=message_bus)


def provide_add_config_to_library_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> AddConfigToLibraryCommand:
    """Provide AddConfigToLibraryCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured AddConfigToLibraryCommand instance

    """
    return AddConfigToLibraryCommand(uow_factory=uow_factory, message_bus=message_bus)


def provide_remove_config_from_library_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> RemoveConfigFromLibraryCommand:
    """Provide RemoveConfigFromLibraryCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured RemoveConfigFromLibraryCommand instance

    """
    return RemoveConfigFromLibraryCommand(uow_factory=uow_factory, message_bus=message_bus)
