"""Read models for Query entities (CQRS pattern)."""

from dataclasses import dataclass
from datetime import datetime

from .search_read_models import SearchResultReadModel


@dataclass(frozen=True)
class QueryReadModel:
    """Read model for Query query results.

    Following CQRS:
    - Separate from domain entity
    - Optimized for query performance
    - Contains denormalized result data
    """

    id: str  # Query ID (UUID as string)
    library_id: str  # Parent library UUID
    vectorization_config_id: str  # Config used for query
    query_text: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    top_k: int
    min_similarity: float
    results: list[SearchResultReadModel] | None  # Populated when COMPLETED
    error_message: str | None  # Populated when FAILED
    created_at: datetime
    updated_at: datetime
