"""Document queries for read operations (CQRS pattern)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetDocumentsQuery:
    """Query to get all documents in a library.

    Following CQRS:
    - Queries are immutable
    - Contains only filter/pagination params
    - No business logic
    """

    library_id: str  # UUID string
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetDocumentByIdQuery:
    """Query to get a document by ID.

    Attributes:
        library_id: The parent library's unique identifier (UUID string)
        document_id: The document's unique identifier (UUID string)

    """

    library_id: str
    document_id: str


@dataclass(frozen=True)
class GetDocumentChunksQuery:
    """Query to get all chunks for a document.

    Following CQRS:
    - Queries are immutable
    - Contains only filter/pagination params
    - No business logic

    Attributes:
        library_id: The parent library's unique identifier (UUID string)
        document_id: The document's unique identifier (UUID string)
        limit: Maximum number of chunks to return
        offset: Number of chunks to skip for pagination

    """

    library_id: str
    document_id: str
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetDocumentFragmentsQuery:
    """Query to get all fragments for a document.

    Following CQRS:
    - Queries are immutable
    - Contains only filter/pagination params
    - No business logic

    Attributes:
        library_id: The parent library's unique identifier (UUID string)
        document_id: The document's unique identifier (UUID string)
        limit: Maximum number of fragments to return
        offset: Number of fragments to skip for pagination

    """

    library_id: str
    document_id: str
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetDocumentVectorizationStatusQuery:
    """Query to get vectorization status for a document.

    Returns the processing status for each VectorizationConfig
    that this document is being processed with.

    Following CQRS:
    - Queries are immutable
    - Contains only filter params
    - No business logic

    Attributes:
        library_id: The parent library's unique identifier (UUID string)
        document_id: The document's unique identifier (UUID string)

    """

    library_id: str
    document_id: str
