"""Storage provider enumeration for simplified SDK configuration."""

from enum import StrEnum, auto


class StorageProvider(StrEnum):
    """High-level storage provider modes for SDK configuration.

    This is a simplified enum for SDK users who don't need to know
    about specific backend implementations (DuckDB, PostgreSQL, etc.).

    Values:
        IN_MEMORY: In-memory storage (default, for development/testing)
            - Fast, ephemeral, no persistence
            - Uses inmemory StorageType internally
        REMOTE: Remote/persistent storage (production)
            - Durable, requires database connection
            - Maps to postgres/duckdb StorageType based on database_url

    Example:
        >>> from vdb_sdk import VectorDBClient, StorageProvider
        >>> client = VectorDBClient(storage=StorageProvider.IN_MEMORY)

    """

    IN_MEMORY = auto()
    REMOTE = auto()
