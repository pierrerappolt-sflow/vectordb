"""In-memory Unit of Work implementation for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from vdb_core.application.i_unit_of_work import IUnitOfWork
from vdb_core.infrastructure.repositories import InMemoryLibraryRepository

if TYPE_CHECKING:
    from types import TracebackType

    from vdb_core.domain.entities import Library
    from vdb_core.domain.events import DomainEvent
    from vdb_core.domain.repositories import ILibraryRepository

# Singleton storage shared across all UoW instances (for in-memory CQRS)
# This ensures write operations are visible to read operations immediately
_SHARED_LIBRARY_STORAGE: dict[str, Library] = {}


class InMemoryUnitOfWork(IUnitOfWork):
    """In-memory implementation of Unit of Work.

    Provides transaction-like semantics for in-memory storage.
    Since there's no real database, commit/rollback are simpler.

    Following Cosmic Python pattern:
    - Repositories track entities in `self.seen`
    - UoW collects events from tracked entities on commit
    - Events returned only after successful commit

    Example:
        async with uow:
            library = Library(name=LibraryName("Test"))
            await uow.libraries.add(library)

            events = await uow.commit()  # Collects events from library
            # Events published after commit

    """

    def __init__(self) -> None:
        """Initialize Unit of Work with Library aggregate root repository.

        Note: Uses module-level shared storage to ensure CQRS read/write consistency.
        All UoW instances share the same underlying storage, allowing immediate visibility
        of write operations to read operations.
        """
        # Only 1 aggregate root repository
        self.libraries: ILibraryRepository = InMemoryLibraryRepository(shared_storage=_SHARED_LIBRARY_STORAGE)  # type: ignore[assignment]
        self._committed = False

    async def __aenter__(self) -> Self:
        """Start transaction context.

        For in-memory implementation, just clear the seen sets.
        """
        # Clear seen sets from previous transactions
        self.libraries.seen.clear()
        self.libraries.added.clear()
        self._committed = False
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Exit transaction context with automatic rollback on error.

        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred

        """
        if exc_type is not None:
            # Exception occurred - rollback
            await self.rollback()
        elif not self._committed:
            # No exception but commit wasn't called - rollback
            await self.rollback()

    async def commit(self) -> list[DomainEvent]:
        """Commit changes and return collected events.

        Following Cosmic Python pattern:
        1. Collect events from all tracked entities (in `self.libraries.seen`)
        2. For in-memory: no actual persistence needed
        3. Clear events from entities
        4. Return events for publication

        Returns:
            List of domain events collected from all tracked entities

        """
        # Collect events from all tracked libraries
        events = self.collect_events()

        # Mark as committed
        self._committed = True

        return events

    async def rollback(self) -> None:
        """Rollback changes.

        For in-memory implementation:
        - Clear the seen sets
        - Clear events from tracked entities
        - In real implementation: rollback database transaction
        """
        # Clear events from Library aggregate root
        for library in self.libraries.seen:
            library.events.clear()

        # Clear seen sets
        self.libraries.seen.clear()
        self.libraries.added.clear()

        self._committed = False

    def collect_events(self) -> list[DomainEvent]:
        """Collect events from all tracked aggregate roots.

        Following Cosmic Python + DDD:
        - Iterate over `self.libraries.seen`
        - Call `aggregate.collect_all_events()` to get events from aggregate tree
        - Library events: Library → Documents → Fragments → Chunks

        Returns:
            List of domain events from all tracked aggregates

        """
        all_events: list[DomainEvent] = []

        # Collect from Library aggregates
        for library in self.libraries.seen:
            aggregate_events = library.collect_all_events()
            all_events.extend(aggregate_events)

        return all_events
