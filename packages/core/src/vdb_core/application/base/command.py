"""Base command interface for CQRS pattern with generic type parameters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.message_bus import IMessageBus

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class Command[TInput, TOutput](ABC):
    """Base class for all command handlers in the application.

    Commands represent write operations that change system state.
    They follow the Command pattern and are part of the CQRS architecture.

    This base class provides a template method pattern for UoW + event handling:
    - execute() orchestrates the transaction and event publishing
    - _execute_business_logic() contains the actual domain logic (abstract)

    Type Parameters:
        TInput: Type of input data
        TOutput: Type of output data

    Example:
        class CreateLibraryInput:
            name: str

        class CreateLibraryCommand(Command[CreateLibraryInput, LibraryId]):
            async def _execute(
                self, input_data: CreateLibraryInput, uow: IUnitOfWork
            ) -> LibraryId:
                library = Library(name=LibraryName(value=input_data.name))
                await uow.libraries.add(library)
                return library.id

        # Usage:
        command = CreateLibraryCommand(uow_factory, bus)
        library_id = await command.execute(CreateLibraryInput(name="Test"))

    """

    def __init__(self, uow_factory: Callable[[], IUnitOfWork], message_bus: IMessageBus) -> None:
        """Initialize command with dependencies.

        Args:
            uow_factory: Factory function that creates UoW instances
            message_bus: Message bus for routing events to handlers

        """
        self.uow_factory = uow_factory
        self.message_bus = message_bus

    async def execute(self, input_data: TInput) -> TOutput:
        """Execute the command with typed input.

        This template method:
        1. Creates a UoW
        2. Opens a transaction
        3. Calls _execute() (implemented by subclasses)
        4. Commits the transaction
        5. Publishes collected domain events

        Args:
            input_data: Typed input data for the command

        Returns:
            Typed output/result data

        Raises:
            DomainException: If domain validation fails
            ApplicationException: If application-level validation fails

        """
        uow = self.uow_factory()
        async with uow:
            result = await self._execute(input_data, uow)
            events = await uow.commit()

        await self.message_bus.handle_events(events)

        return result

    @abstractmethod
    async def _execute(self, input_data: TInput, uow: IUnitOfWork) -> TOutput:
        """Execute the command's business logic.

        This method is called within a UoW transaction context.
        Subclasses implement their domain logic here.

        Args:
            input_data: Typed input data for the command
            uow: Active Unit of Work (within transaction)

        Returns:
            Typed output/result data

        Raises:
            DomainException: If domain validation fails
            ApplicationException: If application-level validation fails

        """
        ...
