"""Dependency injection providers for document commands."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from vdb_core.application.commands import (
    CreateDocumentCommand,
    CreateDocumentFragmentCommand,
    DeleteDocumentCommand,
    UpdateDocumentCommand,
    UploadDocumentCommand,
)

if TYPE_CHECKING:
    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.message_bus import IMessageBus


def provide_create_document_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> CreateDocumentCommand:
    """Provide CreateDocumentCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured CreateDocumentCommand instance

    """
    return CreateDocumentCommand(uow_factory=uow_factory, message_bus=message_bus)


def provide_update_document_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> UpdateDocumentCommand:
    """Provide UpdateDocumentCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured UpdateDocumentCommand instance

    """
    return UpdateDocumentCommand(uow_factory=uow_factory, message_bus=message_bus)


def provide_delete_document_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> DeleteDocumentCommand:
    """Provide DeleteDocumentCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured DeleteDocumentCommand instance

    """
    return DeleteDocumentCommand(uow_factory=uow_factory, message_bus=message_bus)


def provide_upload_document_command(
    create_document_command: CreateDocumentCommand,
    create_fragment_command: CreateDocumentFragmentCommand,
) -> UploadDocumentCommand:
    """Provide UploadDocumentCommand with its dependencies.

    Args:
        create_document_command: Command for creating documents
        create_fragment_command: Command for creating document fragments

    Returns:
        Configured UploadDocumentCommand instance

    """
    return UploadDocumentCommand(
        create_document_command=create_document_command,
        create_fragment_command=create_fragment_command,
    )


def provide_create_document_fragment_command(
    uow_factory: Callable[[], "IUnitOfWork"], message_bus: "IMessageBus"
) -> CreateDocumentFragmentCommand:
    """Provide CreateDocumentFragmentCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured CreateDocumentFragmentCommand instance

    """
    return CreateDocumentFragmentCommand(uow_factory=uow_factory, message_bus=message_bus)
