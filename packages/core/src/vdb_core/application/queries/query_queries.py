"""Query queries for read operations (CQRS pattern)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetQueriesQuery:
    """Query to get all queries for a library.

    Following CQRS:
    - Queries are immutable
    - Contains only filter/pagination params
    - No business logic

    Attributes:
        library_id: The library's unique identifier (UUID string)
        limit: Maximum number of queries to return
        offset: Number of queries to skip for pagination

    """

    library_id: str  # UUID string
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetQueryByIdQuery:
    """Query to get a specific query by ID.

    Attributes:
        library_id: The parent library's unique identifier (UUID string)
        query_id: The query's unique identifier (UUID string)

    """

    library_id: str
    query_id: str
