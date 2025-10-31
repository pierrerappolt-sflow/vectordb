"""Library queries for read operations (CQRS pattern)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetLibrariesQuery:
    """Query to get all libraries.

    Following CQRS:
    - Queries are immutable
    - Contains only filter/pagination params
    - No business logic
    """

    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetLibraryByIdQuery:
    """Query to get a library by ID.

    Attributes:
        library_id: The library's unique identifier (UUID string)

    """

    library_id: str


@dataclass(frozen=True)
class GetLibraryConfigsQuery:
    """Query to get all vectorization configs for a library.

    Following CQRS:
    - Queries are immutable
    - Contains only filter params
    - No business logic

    Attributes:
        library_id: The library's unique identifier (UUID string)

    """

    library_id: str
