"""Application container for Commands and QueryHandlers."""

from typing import TYPE_CHECKING

from vdb_core.application.commands import (
    AddConfigToLibraryCommand,
    CreateDocumentCommand,
    CreateDocumentFragmentCommand,
    CreateLibraryCommand,
    DeleteDocumentCommand,
    DeleteLibraryCommand,
    ParseDocumentCommand,
    ProcessVectorizationConfigCommand,
    RemoveConfigFromLibraryCommand,
    UpdateDocumentCommand,
    UpdateLibraryCommand,
    UploadDocumentCommand,
)
from vdb_core.application.query_handlers import (
    GetDocumentByIdQuery,
    GetDocumentChunksQuery,
    GetDocumentFragmentsQuery,
    GetDocumentsQuery,
    GetDocumentVectorizationStatusQuery,
    GetEventLogByIdQuery,
    GetEventLogsQuery,
    GetLibrariesQuery,
    GetLibraryByIdQuery,
    GetLibraryConfigsQuery,
    GetQueriesQuery,
    GetQueryByIdQuery,
)
from vdb_core.infrastructure.di import commands

from .base_container import BaseContainer

if TYPE_CHECKING:
    from .di_container import DIContainer


class ApplicationContainer(BaseContainer):
    """Container for application layer Commands and QueryHandlers."""

    def __init__(self, main_container: "DIContainer") -> None:
        """Initialize application container.

        Args:
            main_container: Main DI container for resolving dependencies

        """
        super().__init__()
        self.container = main_container

    # ==================== Commands (Write Side) ====================

    @property
    def create_library_command(self) -> CreateLibraryCommand:
        """Get the create library command (singleton)."""

        def factory() -> CreateLibraryCommand:
            return commands.provide_create_library_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
                config_read_repo_factory=self.container.get_vectorization_config_read_repository,
            )

        return self._get_or_create("create_library_command", factory)

    @property
    def update_library_command(self) -> UpdateLibraryCommand:
        """Get the update library command (singleton)."""

        def factory() -> UpdateLibraryCommand:
            return commands.provide_update_library_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("update_library_command", factory)

    @property
    def delete_library_command(self) -> DeleteLibraryCommand:
        """Get the delete library command (singleton)."""

        def factory() -> DeleteLibraryCommand:
            return commands.provide_delete_library_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("delete_library_command", factory)

    @property
    def add_config_to_library_command(self) -> AddConfigToLibraryCommand:
        """Get the add config to library command (singleton)."""

        def factory() -> AddConfigToLibraryCommand:
            return commands.provide_add_config_to_library_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("add_config_to_library_command", factory)

    @property
    def remove_config_from_library_command(self) -> RemoveConfigFromLibraryCommand:
        """Get the remove config from library command (singleton)."""

        def factory() -> RemoveConfigFromLibraryCommand:
            return commands.provide_remove_config_from_library_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("remove_config_from_library_command", factory)

    @property
    def create_document_command(self) -> CreateDocumentCommand:
        """Get the create document command (singleton)."""

        def factory() -> CreateDocumentCommand:
            return commands.provide_create_document_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("create_document_command", factory)

    @property
    def update_document_command(self) -> UpdateDocumentCommand:
        """Get the update document command (singleton)."""

        def factory() -> UpdateDocumentCommand:
            return commands.provide_update_document_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("update_document_command", factory)

    @property
    def delete_document_command(self) -> DeleteDocumentCommand:
        """Get the delete document command (singleton)."""

        def factory() -> DeleteDocumentCommand:
            return commands.provide_delete_document_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("delete_document_command", factory)

    @property
    def create_document_fragment_command(self) -> CreateDocumentFragmentCommand:
        """Get the create document fragment command (singleton)."""

        def factory() -> CreateDocumentFragmentCommand:
            return commands.provide_create_document_fragment_command(
                uow_factory=self.container.get_unit_of_work,
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("create_document_fragment_command", factory)

    @property
    def upload_document_command(self) -> UploadDocumentCommand:
        """Get the upload document command (singleton)."""

        def factory() -> UploadDocumentCommand:
            return commands.provide_upload_document_command(
                create_document_command=self.create_document_command,
                create_fragment_command=self.create_document_fragment_command,
            )

        return self._get_or_create("upload_document_command", factory)

    @property
    def parse_document_command(self) -> ParseDocumentCommand:
        """Get the parse document command (singleton).

        This command is used by Temporal activities for document parsing.
        """

        def factory() -> ParseDocumentCommand:
            return commands.provide_parse_document_command(
                uow_factory=lambda: self.container.get_unit_of_work(),
                message_bus=self.container.get_message_bus(),
                parser=self.container.get_parser(),
            )

        return self._get_or_create("parse_document_command", factory)

    @property
    def process_vectorization_config_command(self) -> ProcessVectorizationConfigCommand:
        """Get the process vectorization config command (singleton).

        This command is used by Temporal activities for vectorization processing.
        """

        def factory() -> ProcessVectorizationConfigCommand:
            return commands.provide_process_vectorization_config_command(
                uow=self.container.get_unit_of_work(),
                message_bus=self.container.get_message_bus(),
            )

        return self._get_or_create("process_vectorization_config_command", factory)

    # ==================== Queries (Read Side) ====================
    # Following Command pattern: Queries take read_repo_provider_factory

    @property
    def get_libraries_query(self) -> GetLibrariesQuery:
        """Get the get libraries query (singleton)."""

        def factory() -> GetLibrariesQuery:
            return GetLibrariesQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_libraries_query", factory)

    @property
    def get_library_by_id_query(self) -> GetLibraryByIdQuery:
        """Get the get library by ID query (singleton)."""

        def factory() -> GetLibraryByIdQuery:
            return GetLibraryByIdQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_library_by_id_query", factory)

    @property
    def get_documents_query(self) -> GetDocumentsQuery:
        """Get the get documents query (singleton)."""

        def factory() -> GetDocumentsQuery:
            return GetDocumentsQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_documents_query", factory)

    @property
    def get_document_by_id_query(self) -> GetDocumentByIdQuery:
        """Get the get document by ID query (singleton)."""

        def factory() -> GetDocumentByIdQuery:
            return GetDocumentByIdQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_document_by_id_query", factory)

    @property
    def get_document_chunks_query(self) -> GetDocumentChunksQuery:
        """Get the get document chunks query (singleton)."""

        def factory() -> GetDocumentChunksQuery:
            return GetDocumentChunksQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_document_chunks_query", factory)

    @property
    def get_event_logs_query(self) -> GetEventLogsQuery:
        """Get the get event logs query (singleton)."""

        def factory() -> GetEventLogsQuery:
            return GetEventLogsQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_event_logs_query", factory)

    @property
    def get_event_log_by_id_query(self) -> GetEventLogByIdQuery:
        """Get the get event log by ID query (singleton)."""

        def factory() -> GetEventLogByIdQuery:
            return GetEventLogByIdQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_event_log_by_id_query", factory)

    @property
    def get_library_configs_query(self) -> GetLibraryConfigsQuery:
        """Get the get library configs query (singleton)."""

        def factory() -> GetLibraryConfigsQuery:
            return GetLibraryConfigsQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_library_configs_query", factory)

    @property
    def get_document_fragments_query(self) -> GetDocumentFragmentsQuery:
        """Get the get document fragments query (singleton)."""

        def factory() -> GetDocumentFragmentsQuery:
            return GetDocumentFragmentsQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_document_fragments_query", factory)

    @property
    def get_document_vectorization_status_query(self) -> GetDocumentVectorizationStatusQuery:
        """Get the get document vectorization status query (singleton)."""

        def factory() -> GetDocumentVectorizationStatusQuery:
            return GetDocumentVectorizationStatusQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_document_vectorization_status_query", factory)

    @property
    def get_queries_query(self) -> GetQueriesQuery:
        """Get the get queries query (singleton)."""

        def factory() -> GetQueriesQuery:
            return GetQueriesQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_queries_query", factory)

    @property
    def get_query_by_id_query(self) -> GetQueryByIdQuery:
        """Get the get query by ID query (singleton)."""

        def factory() -> GetQueryByIdQuery:
            return GetQueryByIdQuery(
                read_repo_provider_factory=self.container.get_read_repository_provider,
            )

        return self._get_or_create("get_query_by_id_query", factory)

