"""Factory for creating infrastructure implementations based on configuration."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg

from vdb_core.application.i_unit_of_work import IUnitOfWork
from vdb_core.application.message_bus import IMessageBus
from vdb_core.application.repositories import (
    IChunkReadRepository,
    IDocumentFragmentReadRepository,
    IDocumentReadRepository,
    IEventLogReadRepository,
    ILibraryReadRepository,
    IVectorizationConfigReadRepository,
)
from vdb_core.infrastructure.config import AppConfig
from vdb_core.infrastructure.config.config_models import MessageBusType, ReadModelType, StorageType
from vdb_core.infrastructure.message_bus import InMemoryMessageBus
from vdb_core.infrastructure.persistence import InMemoryUnitOfWork
from vdb_core.infrastructure.repositories import (
    InMemoryDocumentReadRepository,
    InMemoryEventLogReadRepository,
    InMemoryLibraryReadRepository,
    PostgresDocumentReadRepository,
    PostgresEventLogReadRepository,
)


class InfrastructureFactory:
    """Factory for creating infrastructure implementations based on configuration.

    Following Factory pattern:
    - Encapsulates object creation logic
    - Allows switching implementations via config
    - Makes adding new implementations easy

    Example:
        config = load_config()
        factory = InfrastructureFactory(config)
        uow = factory.create_unit_of_work()
        message_bus = factory.create_message_bus()

    """

    def __init__(self, config: AppConfig) -> None:
        """Initialize factory with configuration.

        Args:
            config: Application configuration

        """
        self.config = config
        self._pg_read_pool = None  # Shared Postgres connection pool for read repositories
        self._pg_write_pool = None  # Shared Postgres connection pool for write operations (UoW)

    async def _get_or_create_pg_read_pool(self) -> "asyncpg.Pool":
        """Get or create shared Postgres connection pool for read repositories.

        Returns:
            asyncpg.Pool: Shared connection pool

        Raises:
            ValueError: If DATABASE_URL not configured

        """
        if self._pg_read_pool is None:
            import os

            import asyncpg

            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                msg = "DATABASE_URL environment variable required for Postgres read repositories"
                raise ValueError(msg)

            # Remove asyncpg driver prefix if present
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

            self._pg_read_pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)

        return self._pg_read_pool

    async def _get_or_create_pg_write_pool(self) -> "asyncpg.Pool":
        """Get or create shared Postgres connection pool for write operations (UoW).

        Returns:
            asyncpg.Pool: Shared connection pool

        Raises:
            ValueError: If DATABASE_URL not configured

        """
        if self._pg_write_pool is None:
            import os

            import asyncpg

            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                msg = "DATABASE_URL environment variable required for Postgres storage"
                raise ValueError(msg)

            # Remove asyncpg driver prefix if present
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

            # Larger pool for write operations since they're transactional
            self._pg_write_pool = await asyncpg.create_pool(database_url, min_size=5, max_size=20)

        return self._pg_write_pool

    def create_unit_of_work(self) -> IUnitOfWork:
        """Create Unit of Work based on configuration.

        Returns:
            IUnitOfWork implementation

        Raises:
            NotImplementedError: If storage type not yet implemented

        """
        storage_type = self.config.get_storage_type()

        if storage_type == StorageType.INMEMORY:
            return InMemoryUnitOfWork()
        if storage_type == StorageType.DUCKDB:
            # TODO(pierre): Implement DuckDB UnitOfWork
            msg = f"Storage type {storage_type} not yet implemented"
            raise NotImplementedError(msg)
        if storage_type == StorageType.POSTGRES:
            from vdb_core.infrastructure.persistence import PostgresUnitOfWork

            # PostgresUnitOfWork now uses DatabaseSessionManager internally
            # which handles the shared engine and session maker
            return PostgresUnitOfWork()
        msg = f"Unknown storage type: {storage_type}"
        raise ValueError(msg)

    def create_message_bus(self) -> IMessageBus:
        """Create Message Bus based on configuration.

        Returns:
            IMessageBus implementation

        Raises:
            NotImplementedError: If message bus type not yet implemented

        """
        bus_type = self.config.get_message_bus_type()

        if bus_type == MessageBusType.INMEMORY:
            return InMemoryMessageBus()
        if bus_type == MessageBusType.RABBITMQ:
            from urllib.parse import urlparse

            from vdb_core.infrastructure.message_bus import RabbitMQMessageBus

            # Parse broker_url or use defaults
            broker_url = self.config.infrastructure.message_bus.broker_url
            if broker_url:
                # Parse amqp://user:pass@host:port/vhost
                parsed = urlparse(broker_url)
                return RabbitMQMessageBus(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 5672,
                    username=parsed.username or "guest",
                    password=parsed.password or "guest",
                    virtual_host=parsed.path.lstrip("/") or "/",
                )
            # Use defaults
            return RabbitMQMessageBus()
        if bus_type == MessageBusType.KAFKA:
            # TODO(pierre): Implement Kafka MessageBus
            msg = f"Message bus type {bus_type} not yet implemented"
            raise NotImplementedError(msg)
        msg = f"Unknown message bus type: {bus_type}"
        raise ValueError(msg)

    def create_library_read_repository(self, write_storage: dict[Any, Any] | None = None) -> ILibraryReadRepository:
        """Create Library Read Repository based on configuration.

        Args:
            write_storage: Reference to write storage (for shared in-memory storage mode)

        Returns:
            ILibraryReadRepository implementation

        Raises:
            NotImplementedError: If read model type not yet implemented

        """
        read_type = self.config.get_read_model_type()

        if isinstance(read_type, StorageType):
            # Shared read/write storage
            if read_type == StorageType.INMEMORY:
                if not write_storage:
                    msg = "write_storage required for in-memory storage"
                    raise ValueError(msg)
                return InMemoryLibraryReadRepository(write_storage=write_storage)
            if read_type == StorageType.POSTGRES:
                # Use postgres read repository (queries database directly)
                import os

                from vdb_core.infrastructure.repositories.read import PostgresLibraryReadRepository

                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    msg = "DATABASE_URL environment variable required for Postgres read repository"
                    raise ValueError(msg)
                return PostgresLibraryReadRepository(database_url)
            msg = f"Shared storage type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        if isinstance(read_type, ReadModelType):
            # Separate read model store
            if read_type == ReadModelType.INMEMORY:
                if not write_storage:
                    msg = "write_storage required for in-memory read models"
                    raise ValueError(msg)
                return InMemoryLibraryReadRepository(write_storage=write_storage)
            if read_type == ReadModelType.REDIS:
                # TODO(pierre): Implement Redis LibraryReadRepository
                msg = f"Read model type {read_type} not yet implemented"
                raise NotImplementedError(msg)
            msg = f"Read model type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        msg = f"Unknown read model type: {read_type}"
        raise ValueError(msg)

    def create_document_read_repository(self, library_storage: dict[Any, Any] | None = None) -> IDocumentReadRepository:
        """Create Document Read Repository based on configuration.

        Args:
            library_storage: Reference to library storage (for shared in-memory storage mode)

        Returns:
            IDocumentReadRepository implementation

        Raises:
            NotImplementedError: If read model type not yet implemented

        """
        read_type = self.config.get_read_model_type()

        if isinstance(read_type, StorageType):
            # Shared read/write storage
            if read_type == StorageType.INMEMORY:
                if not library_storage:
                    msg = "library_storage required for in-memory storage"
                    raise ValueError(msg)
                return InMemoryDocumentReadRepository(library_storage=library_storage)
            if read_type == StorageType.POSTGRES:
                # Use postgres read repository (queries database directly)
                import os

                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    msg = "DATABASE_URL environment variable required for Postgres read repository"
                    raise ValueError(msg)
                return PostgresDocumentReadRepository(database_url)
            msg = f"Shared storage type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        if isinstance(read_type, ReadModelType):
            # Separate read model store
            if read_type == ReadModelType.INMEMORY:
                if not library_storage:
                    msg = "library_storage required for in-memory read models"
                    raise ValueError(msg)
                return InMemoryDocumentReadRepository(library_storage=library_storage)
            msg = f"Read model type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        msg = f"Unknown read model type: {read_type}"
        raise ValueError(msg)

    def create_chunk_read_repository(self, library_storage: dict[Any, Any]) -> IChunkReadRepository:
        """Create Chunk Read Repository based on configuration.

        Args:
            library_storage: Reference to library storage (for shared storage mode)

        Returns:
            IChunkReadRepository implementation

        Raises:
            NotImplementedError: If read model type not yet implemented

        """
        from vdb_core.infrastructure.repositories import InMemoryChunkReadRepository

        read_type = self.config.get_read_model_type()

        if isinstance(read_type, StorageType):
            # Shared read/write storage
            if read_type == StorageType.INMEMORY:
                return InMemoryChunkReadRepository(library_storage=library_storage)
            if read_type == StorageType.POSTGRES:
                # Use postgres read repository - pool created lazily on first use
                import os

                from vdb_core.infrastructure.repositories.read import PostgresChunkReadRepository

                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    msg = "DATABASE_URL environment variable required for Postgres read repository"
                    raise ValueError(msg)

                # Remove asyncpg driver prefix if present
                if database_url.startswith("postgresql+asyncpg://"):
                    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

                return PostgresChunkReadRepository(database_url)
            msg = f"Shared storage type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        if isinstance(read_type, ReadModelType):
            # Separate read model store
            if read_type == ReadModelType.INMEMORY:
                return InMemoryChunkReadRepository(library_storage=library_storage)
            msg = f"Read model type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        msg = f"Unknown read model type: {read_type}"
        raise ValueError(msg)

    def create_document_fragment_read_repository(self) -> IDocumentFragmentReadRepository:
        """Create Document Fragment Read Repository based on configuration.

        Returns:
            IDocumentFragmentReadRepository implementation

        Raises:
            NotImplementedError: If read model type not yet implemented

        """
        read_type = self.config.get_read_model_type()

        if isinstance(read_type, StorageType):
            # Shared read/write storage
            if read_type == StorageType.POSTGRES:
                # Use postgres read repository - pool created lazily on first use
                import os

                from vdb_core.infrastructure.repositories.read import PostgresDocumentFragmentReadRepository

                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    msg = "DATABASE_URL environment variable required for Postgres read repository"
                    raise ValueError(msg)

                # Remove asyncpg driver prefix if present
                if database_url.startswith("postgresql+asyncpg://"):
                    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

                return PostgresDocumentFragmentReadRepository(database_url)
            msg = f"Shared storage type {read_type} not yet implemented for DocumentFragmentReadRepository"
            raise NotImplementedError(msg)
        if isinstance(read_type, ReadModelType):
            # Separate read model store
            msg = f"Read model type {read_type} not yet implemented for DocumentFragmentReadRepository"
            raise NotImplementedError(msg)
        msg = f"Unknown read model type: {read_type}"
        raise ValueError(msg)

    def create_event_log_read_repository(self, unit_of_work: IUnitOfWork | None = None) -> IEventLogReadRepository:
        """Create EventLog Read Repository based on configuration.

        Args:
            unit_of_work: Unit of work for accessing event storage (for in-memory mode)

        Returns:
            IEventLogReadRepository implementation

        Raises:
            NotImplementedError: If read model type not yet implemented

        """
        read_type = self.config.get_read_model_type()

        if isinstance(read_type, StorageType):
            # Shared read/write storage
            if read_type == StorageType.INMEMORY:
                if not unit_of_work:
                    msg = "unit_of_work required for in-memory storage"
                    raise ValueError(msg)
                return InMemoryEventLogReadRepository(unit_of_work=unit_of_work)
            if read_type == StorageType.POSTGRES:
                # Use postgres read repository (queries database directly)
                import os

                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    msg = "DATABASE_URL environment variable required for Postgres read repository"
                    raise ValueError(msg)
                return PostgresEventLogReadRepository(database_url)
            msg = f"Shared storage type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        if isinstance(read_type, ReadModelType):
            # Separate read model store
            if read_type == ReadModelType.INMEMORY:
                if not unit_of_work:
                    msg = "unit_of_work required for in-memory read models"
                    raise ValueError(msg)
                return InMemoryEventLogReadRepository(unit_of_work=unit_of_work)
            msg = f"Read model type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        msg = f"Unknown read model type: {read_type}"
        raise ValueError(msg)

    def create_vectorization_config_read_repository(self) -> IVectorizationConfigReadRepository:
        """Create VectorizationConfig Read Repository based on configuration.

        Returns:
            IVectorizationConfigReadRepository implementation

        Raises:
            NotImplementedError: If read model type not yet implemented

        """
        read_type = self.config.get_read_model_type()

        if isinstance(read_type, StorageType):
            # Shared read/write storage
            if read_type == StorageType.POSTGRES:
                # Use postgres read repository (queries database directly)
                import os

                from vdb_core.infrastructure.repositories.read import (
                    PostgresVectorizationConfigReadRepository,
                )

                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    msg = "DATABASE_URL environment variable required for Postgres read repository"
                    raise ValueError(msg)
                return PostgresVectorizationConfigReadRepository(database_url)
            msg = f"Shared storage type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        if isinstance(read_type, ReadModelType):
            # Separate read model store
            msg = f"Read model type {read_type} not yet implemented"
            raise NotImplementedError(msg)
        msg = f"Unknown read model type: {read_type}"
        raise ValueError(msg)
