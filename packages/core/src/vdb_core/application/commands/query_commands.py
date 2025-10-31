"""Query commands for write operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateQueryCommand:
    """Command to create a new semantic search query.

    Attributes:
        library_id: The library's unique identifier (UUID string)
        vectorization_config_id: The config to use for embedding and search (UUID string)
        query_text: The search query text
        top_k: Number of top results to return (default: 10)
        min_similarity: Minimum similarity threshold 0.0-1.0 (default: 0.0)

    """

    library_id: str
    vectorization_config_id: str
    query_text: str
    top_k: int = 10
    min_similarity: float = 0.0
