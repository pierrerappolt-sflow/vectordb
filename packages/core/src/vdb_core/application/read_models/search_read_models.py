"""Read models for search query results."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResultReadModel:
    """Read model for a single search result.

    Following CQRS:
    - Separate from domain entities
    - Optimized for query responses
    - Contains denormalized data for performance
    """

    chunk_id: str  # Chunk ID
    embedding_id: str  # Embedding ID
    document_id: str  # Parent document ID
    similarity_score: float  # Cosine similarity score (-1.0 to 1.0)
    text: str  # Chunk text content
    start_index: int  # Start position in document
    end_index: int  # End position in document
