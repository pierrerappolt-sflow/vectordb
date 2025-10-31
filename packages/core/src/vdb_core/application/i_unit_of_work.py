"""Unit of Work interface for managing transactions and event collection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType

    from vdb_core.domain.events import DomainEvent
    from vdb_core.domain.repositories import ILibraryRepository, IVectorizationConfigRepository


class IUnitOfWork(ABC):
    """Manages atomic transactions with automatic rollback.

    Following Cosmic Python pattern:
    1. Repository maintains `seen` set to track aggregates
    2. Repositories add entities to their `seen` when they interact with them
    3. `collect_events()` iterates over aggregate `seen` sets and collects from each aggregate's `events` list
    4. Commits all changes atomically (all-or-nothing)
    5. Automatically rolls back on any exception
    6. Returns events only after successful commit

    DDD Aggregate Pattern:
    - 2 write repositories (aggregate roots): Library, VectorizationConfig
    - Documents, Chunks, Fragments: Written through Library aggregate
    - ChunkingStrategy, EmbeddingStrategy: Written through VectorizationConfig aggregate
    - All other entities are either value objects or children of these aggregates

    Usage:
        async with uow:
            # Create and add Library aggregate (documents, chunks, etc. go through this)
            library = Library.create(name=LibraryName(value="My Library"))
            await uow.libraries.add(library)

            # Commit collects events from both aggregate roots
            events = await uow.commit()

            # Publish events only after successful commit
            await event_bus.publish_batch(events)
        # Automatic rollback if any exception occurs
    """

    # Write repositories - 2 aggregate roots
    # IMPORTANT: These are initialized in __aenter__ and MUST only be accessed within async context
    # Outside of async context, these will be uninitialized and accessing them is undefined behavior
    libraries: ILibraryRepository
    vectorization_configs: IVectorizationConfigRepository

    @abstractmethod
    async def __aenter__(self) -> IUnitOfWork:
        """Start a new transaction.

        Acquires database connection/session and begins transaction.

        Returns:
            Self for context manager usage

        """

    @abstractmethod
    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """End transaction with automatic rollback on error.

        If an exception occurred (exc_type is not None), automatically
        calls rollback(). Always cleans up resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred

        """

    @abstractmethod
    async def commit(self) -> list[DomainEvent]:
        """Commit all changes atomically and return domain events.

        This method:
        1. Collects domain events from all tracked entities
        2. Persists all changes to the database atomically
        3. Clears events from entities
        4. Returns collected events for publication

        Events are only returned after successful commit, ensuring
        events are never published for rolled-back transactions.

        Returns:
            List of domain events collected from all entities

        Raises:
            TransactionError: If commit fails (triggers automatic rollback)
            ValidationException: If entity validation fails

        """

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all changes in the current transaction.

        Discards all pending changes and resets the transaction.
        Called automatically by __aexit__ if an exception occurs.

        Raises:
            TransactionError: If rollback fails

        """

    @abstractmethod
    def collect_events(self) -> list[DomainEvent]:
        """Collect domain events from all aggregate roots.

        Following Cosmic Python + DDD patterns:
        - Iterates over all aggregates in both `self.libraries.seen` and `self.vectorization_configs.seen`
        - Calls `aggregate.collect_all_events()` to get events from entire aggregate tree
        - Library events include: Library → Documents → Fragments → Chunks
        - VectorizationConfig events include: VectorizationConfig → ChunkingStrategies → EmbeddingStrategies
        - Events are cleared after collection

        Called internally by commit() before persisting changes.

        Returns:
            List of domain events from all tracked aggregates

        Example implementation:
            def collect_events(self):
                events = []

                # Collect from Library aggregates
                for library in self.libraries.seen:
                    aggregate_events = library.collect_all_events()
                    events.extend(aggregate_events)

                # Collect from VectorizationConfig aggregates
                for config in self.vectorization_configs.seen:
                    aggregate_events = config.collect_all_events()
                    events.extend(aggregate_events)

                return events

        """
