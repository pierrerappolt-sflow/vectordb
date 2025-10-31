"""Dependency injection providers for Temporal workflow commands."""

from typing import TYPE_CHECKING

from vdb_core.application.commands import (
    ParseDocumentCommand,
    ProcessVectorizationConfigCommand,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.message_bus import IMessageBus
    from vdb_core.domain.services import IParser


def provide_parse_document_command(
    uow_factory: "Callable[[], IUnitOfWork]",
    message_bus: "IMessageBus",
    parser: "IParser",
) -> ParseDocumentCommand:
    """Provide ParseDocumentCommand with its dependencies.

    Args:
        uow_factory: Factory function that creates UoW instances
        message_bus: Message bus for routing events to handlers
        parser: Service for parsing content (handles modality detection internally)

    Returns:
        Configured ParseDocumentCommand instance

    """
    return ParseDocumentCommand(
        uow_factory=uow_factory,
        message_bus=message_bus,
        parser=parser,
    )


def provide_process_vectorization_config_command(
    uow: "IUnitOfWork",
    message_bus: "IMessageBus",
) -> ProcessVectorizationConfigCommand:
    """Provide ProcessVectorizationConfigCommand with its dependencies.

    Args:
        uow: Unit of Work for transaction management
        message_bus: Message bus for routing events to handlers

    Returns:
        Configured ProcessVectorizationConfigCommand instance

    """
    return ProcessVectorizationConfigCommand(
        uow=uow,
        message_bus=message_bus,
    )
