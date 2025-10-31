"""PostgreSQL implementation of Unit of Work pattern using SQLAlchemy async sessions."""

from typing import TYPE_CHECKING, override

from vdb_core.application.i_unit_of_work import IUnitOfWork
from vdb_core.domain.events import DomainEvent

from .database import DatabaseSessionManager

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker



class PostgresUnitOfWork(IUnitOfWork):
    """PostgreSQL implementation of Unit of Work using SQLAlchemy async sessions.

    Manages database transactions and tracks domain events from entities.

    Following UoW + SQLAlchemy async patterns:
    - Uses shared async_sessionmaker (one engine for entire app)
    - Session created per UoW instance
    - Transaction managed automatically by session
    - Async context manager for clean resource management
    """

    def __init__(
        self, session_maker: "async_sessionmaker[AsyncSession] | None" = None
    ) -> None:
        """Initialize Postgres Unit of Work.

        Args:
            session_maker: Optional async session maker. If not provided,
                          uses the global DatabaseSessionManager singleton.

        """
        self._session_maker = session_maker or DatabaseSessionManager.get_session_maker()
        self.session: AsyncSession | None = None

        # 2 aggregate root repositories - initialized when session is created
        # Type annotations come from IUnitOfWork interface - these are uninitialized until __aenter__
        self.libraries = None  # type: ignore[assignment]
        self.vectorization_configs = None  # type: ignore[assignment]

    async def __aenter__(self) -> "PostgresUnitOfWork":
        """Enter async context - create session and begin transaction."""
        self.session = self._session_maker()
        await self.session.begin()

        # Initialize aggregate root repositories
        from .postgres_library_repository import PostgresLibraryRepository
        from .postgres_strategy_repositories import PostgresVectorizationConfigRepository

        self.libraries = PostgresLibraryRepository(self.session)  # type: ignore[assignment]
        self.vectorization_configs = PostgresVectorizationConfigRepository(self.session)  # type: ignore[assignment]

        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context - rollback if not committed and close session."""
        try:
            # Rollback only if exception occurred (args[0] is exception type)
            if args[0] is not None:
                await self.rollback()
        finally:
            if self.session:
                await self.session.close()
                self.session = None

    @override
    async def commit(self) -> list[DomainEvent]:
        """Commit transaction and collect domain events from tracked entities.

        Returns:
            List of domain events from all tracked entities

        """
        if not self.session:
            msg = "Session not initialized - use async with block"
            raise RuntimeError(msg)

        if not self.libraries or not self.vectorization_configs:
            msg = "Repositories not initialized"
            raise RuntimeError(msg)

        # Persist modified entities from Library aggregate root
        # Library aggregate handles persisting its entire tree: Library → Documents → Fragments → Chunks
        for entity in self.libraries.seen:
            if entity not in self.libraries.added:
                # Type narrowing: seen contains Library entities from ILibraryRepository
                from vdb_core.domain.entities import Library
                assert isinstance(entity, Library), f"Expected Library, got {type(entity)}"
                await self.libraries._update(entity)
            else:
                # Newly added entities may have accumulated events after _add() was called
                # Process any events that were added after initial persistence
                from vdb_core.domain.entities import Library

                from .postgres_library_repository import PostgresLibraryRepository
                assert isinstance(entity, Library), f"Expected Library, got {type(entity)}"
                assert isinstance(self.libraries, PostgresLibraryRepository), "Expected PostgresLibraryRepository"
                if entity.events:
                    await self.libraries._handle_events(entity)

        # Persist modified entities from VectorizationConfig aggregate root
        # VectorizationConfig aggregate handles persisting its tree: VectorizationConfig → ChunkingStrategies → EmbeddingStrategies
        from vdb_core.domain.entities import VectorizationConfig
        for config in self.vectorization_configs.seen:
            if config not in self.vectorization_configs.added:
                # Type narrowing: seen contains VectorizationConfig entities
                assert isinstance(config, VectorizationConfig), f"Expected VectorizationConfig, got {type(config)}"
                await self.vectorization_configs._update(config)

        # Commit transaction FIRST - only collect events if commit succeeds
        await self.session.commit()

        # Collect events from all tracked entities AFTER successful commit
        # This ensures events are only emitted if the transaction succeeded
        # Following Cosmic Python + DDD pattern: iterate over seen entities
        events: list[DomainEvent] = []

        # Collect from Library aggregates (if repository supports tracking)
        if hasattr(self.libraries, "seen"):
            for library in self.libraries.seen:
                aggregate_events = library.collect_all_events()
                events.extend(aggregate_events)

        # Collect from VectorizationConfig aggregates (if repository supports tracking)
        if hasattr(self.vectorization_configs, "seen"):
            for config in self.vectorization_configs.seen:
                aggregate_events = config.collect_all_events()
                events.extend(aggregate_events)

        return events

    @override
    def collect_events(self) -> list[DomainEvent]:
        """Collect domain events from all tracked entities.

        Returns:
            List of domain events from all tracked aggregates

        """
        events: list[DomainEvent] = []

        # Collect from Library aggregates (if repository supports tracking)
        if hasattr(self.libraries, "seen"):
            for library in self.libraries.seen:
                aggregate_events = library.collect_all_events()
                events.extend(aggregate_events)

        # Collect from VectorizationConfig aggregates (if repository supports tracking)
        if hasattr(self.vectorization_configs, "seen"):
            for config in self.vectorization_configs.seen:
                aggregate_events = config.collect_all_events()
                events.extend(aggregate_events)

        return events

    @override
    async def rollback(self) -> None:
        """Rollback transaction and clear events from tracked entities.

        This ensures that events are not emitted if the transaction fails.
        """
        # Clear events from all tracked entities in Library aggregate root
        if self.libraries:
            for library in self.libraries.seen:
                library.events.clear()
            self.libraries.seen.clear()
            self.libraries.added.clear()

        # Clear events from all tracked entities in VectorizationConfig aggregate root
        if self.vectorization_configs:
            for config in self.vectorization_configs.seen:
                config.events.clear()
            self.vectorization_configs.seen.clear()
            self.vectorization_configs.added.clear()

        # Rollback database transaction
        if self.session:
            try:
                await self.session.rollback()
            except Exception:
                # Transaction may already be rolled back
                pass

    async def close(self) -> None:
        """Close session if still open.

        Note: This does NOT close the engine. The engine is managed
        by DatabaseSessionManager and should only be closed on shutdown.
        """
        if self.session:
            await self.session.close()
            self.session = None
