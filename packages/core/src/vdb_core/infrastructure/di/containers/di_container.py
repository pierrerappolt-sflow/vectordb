"""Main DI container that composes all sub-containers."""

from vdb_core.application.i_unit_of_work import IUnitOfWork
from vdb_core.application.message_bus import IMessageBus
from vdb_core.application.read_repository_provider import ReadRepositoryProvider
from vdb_core.application.repositories import (
    IChunkReadRepository,
    IDocumentFragmentReadRepository,
    IDocumentReadRepository,
    IDocumentVectorizationStatusRepository,
    IEventLogReadRepository,
    ILibraryReadRepository,
    IVectorizationConfigReadRepository,
)
from vdb_core.domain.repositories import IEmbeddingReadRepository, ILibraryRepository
from vdb_core.domain.services import IEmbeddingService, IModalityDetector, IParser
from vdb_core.infrastructure.config import AppConfig, load_config_or_default
from vdb_core.infrastructure.factories import InfrastructureFactory
from vdb_core.infrastructure.parsers import CompositeParser, ModalityDetector, TextParser
from vdb_core.infrastructure.repositories import InMemoryEmbeddingReadRepository
from vdb_core.infrastructure.services import InMemoryEmbeddingService
from vdb_core.infrastructure.vector_index import VectorIndexManager

from .application_container import ApplicationContainer
from .base_container import BaseContainer


class DIContainer(BaseContainer):
    """Main dependency injection container.

    Composes all sub-containers and provides infrastructure implementations.
    Uses configuration to determine which implementations to instantiate.

    Following DI + Factory patterns:
    - Container manages lifecycle (singletons)
    - Factory creates instances based on config
    - Config externalizes infrastructure choices
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        """Initialize the main DI container.

        Args:
            config: Optional configuration. If None, loads from config.yaml or uses defaults.

        """
        super().__init__()

        # Load configuration
        self.config = config or load_config_or_default()

        # Create factory for infrastructure implementations
        self.factory = InfrastructureFactory(self.config)

        # Initialize sub-containers
        self.application = ApplicationContainer(main_container=self)

    # ==================== Infrastructure ====================

    def get_unit_of_work(self) -> IUnitOfWork:
        """Get a new Unit of Work instance (NOT a singleton).

        Implementation determined by config.infrastructure.storage.type

        Note: UoW should be created per-transaction, not cached.
        """
        return self.factory.create_unit_of_work()

    def get_message_bus(self) -> IMessageBus:
        """Get the Message Bus (singleton).

        Returns RabbitMQ message bus for publishing domain events.
        Events are consumed by workers that start Temporal workflows.

        Implementation determined by config.infrastructure.message_bus.type
        """

        def factory_fn() -> IMessageBus:
            # Create RabbitMQ bus for event publishing
            return self.factory.create_message_bus()

        return self._get_or_create("message_bus", factory_fn)

    def get_library_read_repository(self) -> ILibraryReadRepository:
        """Get the Library Read Repository (singleton).

        Implementation determined by config.infrastructure.read_models.type
        or config.infrastructure.storage.type if shared_read_write_storage is True.

        Note: Shares storage with write repository for in-memory implementation.
        In production, this would use a separate read model store or read replica.
        """

        def factory_fn() -> ILibraryReadRepository:
            # For in-memory: share storage with write repository
            # For postgres: create read repository that queries database directly
            storage_type = self.config.get_storage_type()
            if storage_type.value == "inmemory":
                # Import the shared storage from the in-memory UoW module
                from vdb_core.infrastructure.persistence.in_memory_unit_of_work import (
                    _SHARED_LIBRARY_STORAGE,
                )

                return self.factory.create_library_read_repository(write_storage=_SHARED_LIBRARY_STORAGE)
            # Postgres/other: read repository creates its own connection pool
            return self.factory.create_library_read_repository(library_storage=None)

        return self._get_or_create("library_read_repository", factory_fn)

    def get_document_read_repository(self) -> IDocumentReadRepository:
        """Get the Document Read Repository (singleton).

        Implementation determined by config.infrastructure.read_models.type
        or config.infrastructure.storage.type if shared_read_write_storage is True.

        Note: Shares library storage with write repository for in-memory implementation.
        Documents are accessed through their parent Library aggregate.
        """

        def factory_fn() -> IDocumentReadRepository:
            # For in-memory: share storage with write repository
            # For postgres: create read repository that queries database directly
            storage_type = self.config.get_storage_type()
            if storage_type.value == "inmemory":
                uow = self.get_unit_of_work()
                library_storage = uow.libraries._storage
                return self.factory.create_document_read_repository(library_storage=library_storage)
            # Postgres/other: read repository creates its own connection pool
            return self.factory.create_document_read_repository(library_storage=None)

        return self._get_or_create("document_read_repository", factory_fn)

    def get_chunk_read_repository(self) -> IChunkReadRepository:
        """Get the Chunk Read Repository (singleton).

        Implementation determined by config.infrastructure.read_models.type
        or config.infrastructure.storage.type if shared_read_write_storage is True.

        Note: Shares library storage with write repository for in-memory implementation.
        Chunks are accessed through their parent Document entity.
        """

        def factory_fn() -> IChunkReadRepository:
            # For in-memory: share storage with write repository
            # For postgres: create read repository that queries database directly
            storage_type = self.config.get_storage_type()
            if storage_type.value == "inmemory":
                uow = self.get_unit_of_work()
                library_storage = uow.libraries._storage
                return self.factory.create_chunk_read_repository(library_storage=library_storage)
            # Postgres/other: read repository creates its own connection pool
            return self.factory.create_chunk_read_repository(library_storage=None)

        return self._get_or_create("chunk_read_repository", factory_fn)

    def get_document_fragment_read_repository(self) -> IDocumentFragmentReadRepository:
        """Get the Document Fragment Read Repository (singleton).

        Implementation determined by config.infrastructure.read_models.type
        or config.infrastructure.storage.type if shared_read_write_storage is True.

        Note: Document fragments are stored in their own table for streaming upload.
        """

        def factory_fn() -> IDocumentFragmentReadRepository:
            # For postgres: create read repository that queries database directly
            return self.factory.create_document_fragment_read_repository()

        return self._get_or_create("document_fragment_read_repository", factory_fn)

    def get_library_repository(self) -> ILibraryRepository:
        """Get the Library Write Repository (NOT a singleton).

        Returns the library repository from a new Unit of Work.
        Use this for activities that need to load and modify library aggregates.

        Note: Each call creates a new UoW, so you should coordinate with
        the UoW lifecycle in your activity/command handler.
        """
        # Get a new UoW and return its library repository
        # The caller is responsible for committing the UoW
        uow = self.get_unit_of_work()
        return uow.libraries

    def get_event_log_read_repository(self) -> IEventLogReadRepository:
        """Get the Event Log Read Repository (singleton).

        Implementation determined by config.infrastructure.read_models.type
        or config.infrastructure.storage.type if shared_read_write_storage is True.

        Note: Event logs are stored separately from domain aggregates.
        In production, this would query from a dedicated event store.
        """

        def factory_fn() -> IEventLogReadRepository:
            # For in-memory: get UoW to access event log storage
            # For postgres: create read repository that queries database directly
            storage_type = self.config.get_storage_type()
            if storage_type.value == "inmemory":
                uow = self.get_unit_of_work()
                return self.factory.create_event_log_read_repository(unit_of_work=uow)
            # Postgres/other: read repository creates its own connection pool
            return self.factory.create_event_log_read_repository(unit_of_work=None)

        return self._get_or_create("event_log_read_repository", factory_fn)

    def get_vectorization_config_read_repository(self) -> IVectorizationConfigReadRepository:
        """Get the VectorizationConfig Read Repository (singleton).

        Implementation determined by config.infrastructure.read_models.type
        or config.infrastructure.storage.type if shared_read_write_storage is True.

        Note: VectorizationConfigs are global entities stored in their own table.
        """

        def factory_fn() -> IVectorizationConfigReadRepository:
            # For postgres: create read repository that queries database directly
            return self.factory.create_vectorization_config_read_repository()

        return self._get_or_create("vectorization_config_read_repository", factory_fn)

    def get_read_repository_provider(self) -> ReadRepositoryProvider:
        """Get a new Read Repository Provider instance (NOT a singleton).

        Mirrors get_unit_of_work() pattern:
        - Returns NEW instance each time (not cached)
        - Repositories initialized in __aenter__
        - Used with async context manager

        Usage:
            async with container.get_read_repository_provider() as provider:
                configs = await provider.vectorization_configs.get_all()

        Note: ReadRepositoryProvider should be created per-query, not cached.
        """
        from vdb_core.application.read_repository_provider import ReadRepositoryProvider

        return ReadRepositoryProvider(
            library_read_repository_factory=self.get_library_read_repository,
            document_read_repository_factory=self.get_document_read_repository,
            chunk_read_repository_factory=self.get_chunk_read_repository,
            event_log_read_repository_factory=self.get_event_log_read_repository,
            vectorization_config_read_repository_factory=self.get_vectorization_config_read_repository,
            # Optional repositories - will be added when their implementations are wired up
            # document_fragment_read_repository_factory=...,
            # query_read_repository_factory=...,
        )

    def get_embedding_service(self) -> IEmbeddingService:
        """Get the Embedding Service (singleton).

        Uses CohereEmbeddingService for real semantic embeddings.
        Falls back to InMemoryEmbeddingService if COHERE_API_KEY not set.
        """

        def factory_fn() -> IEmbeddingService:
            import os

            from vdb_core.infrastructure.services import CohereEmbeddingService

            api_key = os.getenv("COHERE_API_KEY")
            if api_key:
                return CohereEmbeddingService(api_key)

            return InMemoryEmbeddingService()

        return self._get_or_create("embedding_service", factory_fn)

    def get_vector_repository(self) -> IEmbeddingReadRepository:
        """Get the Vector Repository (singleton).

        For now, uses InMemoryEmbeddingReadRepository with default FLAT indexing.
        In production, this would be replaced with Qdrant/Pinecone/pgvector.
        """

        def factory_fn() -> IEmbeddingReadRepository:
            return InMemoryEmbeddingReadRepository()

        return self._get_or_create("vector_repository", factory_fn)

    def get_vector_index_manager(self) -> VectorIndexManager:
        """Get the Vector Index Manager (singleton).

        Uses PyTorch-based in-memory vector storage with FLAT indexing.
        Supports L2, cosine, and dot product similarity metrics.
        """

        def factory_fn() -> VectorIndexManager:
            return VectorIndexManager()

        return self._get_or_create("vector_index_manager", factory_fn)

    def get_modality_detector(self) -> IModalityDetector:
        """Get the Modality Detector (singleton).

        Uses magic bytes and MIME type detection to identify content type.
        """

        def factory_fn() -> IModalityDetector:
            return ModalityDetector()

        return self._get_or_create("modality_detector", factory_fn)

    def get_parser(self) -> IParser:
        """Get the Parser (singleton).

        Returns CompositeParser that routes to specialized parsers based on content type.
        Currently supports:
        - TextParser for text/plain, text/markdown, etc.
        - PDFParser for application/pdf (placeholder, not yet implemented)
        """

        def factory_fn() -> IParser:
            modality_detector = self.get_modality_detector()
            # Register all available parsers
            parsers: list[IParser] = [
                TextParser(),
                # PDFParser(),  # Not yet implemented
            ]
            return CompositeParser(
                modality_detector=modality_detector,
                parsers=parsers,
            )

        return self._get_or_create("parser", factory_fn)

    def get_document_vectorization_status_repository(
        self,
    ) -> IDocumentVectorizationStatusRepository:
        """Get the Document Vectorization Status Repository (singleton).

        This repository manages the document_vectorization_status tracking table
        for coordinating Temporal workflows across documents and configs.

        Implementation:
        - Postgres: PostgresDocumentVectorizationStatusRepository with own connection pool
        - In-memory: Not yet implemented (would need in-memory tracking)

        """

        def factory_fn() -> IDocumentVectorizationStatusRepository:
            from vdb_core.infrastructure.repositories import (
                PostgresDocumentVectorizationStatusRepository,
            )

            # Get database URL from config
            storage_type = self.config.get_storage_type()
            if storage_type.value == "postgres":
                database_url = self.config.infrastructure.storage.database_url
                if not database_url:
                    msg = "DATABASE_URL not configured for postgres storage"
                    raise ValueError(msg)
                return PostgresDocumentVectorizationStatusRepository(database_url=database_url)

            msg = f"DocumentVectorizationStatusRepository not implemented for {storage_type.value}"
            raise NotImplementedError(msg)

        return self._get_or_create("document_vectorization_status_repository", factory_fn)

    def get_vectorization_orchestration_service(self) -> "VectorizationOrchestrationService":
        """Get the Vectorization Orchestration Service (singleton).

        This service coordinates document vectorization across configs.
        Used by event handlers to schedule processing workflows.

        """
        from vdb_core.application.services.vectorization_orchestration_service import (
            VectorizationOrchestrationService,
        )

        def factory_fn() -> VectorizationOrchestrationService:
            return VectorizationOrchestrationService(
                uow_factory=self.get_unit_of_work,
                status_repository=self.get_document_vectorization_status_repository(),
                document_read_repository=self.get_document_read_repository(),
            )

        return self._get_or_create("vectorization_orchestration_service", factory_fn)

    def get_strategy_resolver(self):  # type: ignore[no-untyped-def]
        """Get strategy resolver for mapping strategy entities to implementations."""
        from vdb_core.infrastructure.strategy_resolution import get_strategy_resolver

        return get_strategy_resolver()

    def get_chunking_service(self):  # type: ignore[no-untyped-def]
        """Get chunking service (deprecated - not implemented)."""
        msg = "ChunkingService not implemented in current architecture"
        raise NotImplementedError(msg)
