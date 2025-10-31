"""Read repository provider for CQRS queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

    from vdb_core.application.repositories import (
        IChunkReadRepository,
        IDocumentFragmentReadRepository,
        IDocumentReadRepository,
        IEventLogReadRepository,
        ILibraryReadRepository,
        IQueryReadRepository,
        IVectorizationConfigReadRepository,
    )


class ReadRepositoryProvider:
    """Provider for all read repositories (CQRS read side)."""

    def __init__(
        self,
        library_read_repository_factory: Callable[[], ILibraryReadRepository],
        document_read_repository_factory: Callable[[], IDocumentReadRepository],
        chunk_read_repository_factory: Callable[[], IChunkReadRepository],
        event_log_read_repository_factory: Callable[[], IEventLogReadRepository],
        vectorization_config_read_repository_factory: Callable[[], IVectorizationConfigReadRepository],
        document_fragment_read_repository_factory: Callable[[], IDocumentFragmentReadRepository] | None = None,
        query_read_repository_factory: Callable[[], IQueryReadRepository] | None = None,
    ) -> None:
        """Initialize provider with repository factories (mirrors UoW pattern).

        Args:
            library_read_repository_factory: Factory for library read repository
            document_read_repository_factory: Factory for document read repository
            chunk_read_repository_factory: Factory for chunk read repository
            event_log_read_repository_factory: Factory for event log read repository
            vectorization_config_read_repository_factory: Factory for vectorization config read repository
            document_fragment_read_repository_factory: Factory for document fragment read repository (optional)
            query_read_repository_factory: Factory for query read repository (optional)

        """
        self._library_read_repository_factory = library_read_repository_factory
        self._document_read_repository_factory = document_read_repository_factory
        self._chunk_read_repository_factory = chunk_read_repository_factory
        self._event_log_read_repository_factory = event_log_read_repository_factory
        self._vectorization_config_read_repository_factory = vectorization_config_read_repository_factory
        self._document_fragment_read_repository_factory = document_fragment_read_repository_factory
        self._query_read_repository_factory = query_read_repository_factory

        # Repositories will be initialized when context is entered (mirrors UoW)
        self.libraries: ILibraryReadRepository | None = None
        self.documents: IDocumentReadRepository | None = None
        self.document_fragments: IDocumentFragmentReadRepository | None = None
        self.chunks: IChunkReadRepository | None = None
        self.queries: IQueryReadRepository | None = None
        self.event_logs: IEventLogReadRepository | None = None
        self.vectorization_configs: IVectorizationConfigReadRepository | None = None

    async def __aenter__(self) -> Self:
        """Enter async context - initialize all repositories (mirrors UoW).

        Returns:
            Self for context manager usage

        """
        # Initialize all repositories from factories (mirrors UoW pattern)
        self.libraries = self._library_read_repository_factory()
        self.documents = self._document_read_repository_factory()
        self.chunks = self._chunk_read_repository_factory()
        self.event_logs = self._event_log_read_repository_factory()
        self.vectorization_configs = self._vectorization_config_read_repository_factory()

        # Optional repositories
        if self._document_fragment_read_repository_factory:
            self.document_fragments = self._document_fragment_read_repository_factory()
        if self._query_read_repository_factory:
            self.queries = self._query_read_repository_factory()

        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Exit async context - cleanup if needed (mirrors UoW).

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred

        """
        # For read-only operations, no rollback needed
        # Just reset repositories to None (mirrors UoW cleanup)
        self.libraries = None
        self.documents = None
        self.document_fragments = None
        self.chunks = None
        self.queries = None
        self.event_logs = None
        self.vectorization_configs = None
