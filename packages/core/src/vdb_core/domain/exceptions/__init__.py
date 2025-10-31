"""Domain exceptions organized by HTTP status codes.

Each exception file maps to a specific HTTP status code:
- validation.py → 400/422 (Bad Request / Unprocessable Entity)
- not_found.py → 404 (Not Found)
- conflict.py → 409 (Conflict)
- transaction.py → 500 (Internal Server Error)
"""

from vdb_core.domain.base import DomainException

# 409 - Conflict Errors
from .conflict import (
    ChunkAlreadyEmbeddedError,
    ConflictException,
    DuplicateModalityError,
    InvalidChunkStatusTransitionError,
)

# 404 - Not Found Errors
from .not_found import (
    ChunkingStrategyNotFoundError,
    ChunkNotFoundError,
    DocumentNotFoundError,
    EmbeddingNotFoundError,
    EmbeddingStrategyNotFoundError,
    EntityNotFoundError,
    LibraryNotFoundError,
    VectorizationConfigNotFoundError,
)

# 500 - Transaction Errors
from .transaction import TransactionError

# 400/422 - Validation Errors
from .validation import (
    ChunkTooLongError,
    DocumentTooLargeError,
    UnsupportedModalityError,
    ValidationException,
)

__all__ = [
    "ChunkAlreadyEmbeddedError",
    "ChunkNotFoundError",
    "ChunkTooLongError",
    "ChunkingStrategyNotFoundError",
    # Conflict (409)
    "ConflictException",
    "DocumentNotFoundError",
    "DocumentTooLargeError",
    # Base
    "DomainException",
    "DuplicateModalityError",
    "EmbeddingNotFoundError",
    "EmbeddingStrategyNotFoundError",
    # Not Found (404)
    "EntityNotFoundError",
    "InvalidChunkStatusTransitionError",
    "LibraryNotFoundError",
    # Transaction (500)
    "TransactionError",
    "UnsupportedModalityError",
    # Validation (400/422)
    "ValidationException",
    "VectorizationConfigNotFoundError",
]
