"""Query handlers for CQRS read operations.

Following Command pattern:
- Queries extend Query[TInput, TOutput] base class
- Take read_repo_provider_factory in __init__
- Execute via async execute(input) method
- Use ReadRepositoryProvider for data access
"""

from .document_query_handlers import (
    GetDocumentByIdQuery,
    GetDocumentChunksQuery,
    GetDocumentFragmentsQuery,
    GetDocumentsQuery,
    GetDocumentVectorizationStatusQuery,
)
from .event_log_query_handlers import GetEventLogByIdQuery, GetEventLogsQuery
from .library_query_handlers import (
    GetLibrariesQuery,
    GetLibraryByIdQuery,
    GetLibraryConfigsQuery,
)
from .query_query_handlers import GetQueriesQuery, GetQueryByIdQuery

__all__ = [
    # Document queries
    "GetDocumentByIdQuery",
    "GetDocumentChunksQuery",
    "GetDocumentFragmentsQuery",
    "GetDocumentsQuery",
    "GetDocumentVectorizationStatusQuery",
    # Event log queries
    "GetEventLogByIdQuery",
    "GetEventLogsQuery",
    # Library queries
    "GetLibrariesQuery",
    "GetLibraryByIdQuery",
    "GetLibraryConfigsQuery",
    # Query queries (yes, really)
    "GetQueriesQuery",
    "GetQueryByIdQuery",
]
