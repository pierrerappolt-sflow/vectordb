"""Conflict exceptions (HTTP 409)."""

from typing import final, override

from vdb_core.domain.base import DomainException


class ConflictException(DomainException):
    """Base exception for business rule conflicts (HTTP 409).

    Raised when operation conflicts with current state:
    - Invalid state transitions
    - Invariant violations
    - Duplicate resource creation
    - Concurrent modification conflicts

    Maps to HTTP 409 Conflict.
    """

    def __init__(self, message: str) -> None:
        """Initialize conflict exception.

        Args:
            message: Description of the conflict

        """
        super().__init__(message)


@final
class InvalidChunkStatusTransitionError(ConflictException):
    """Invalid chunk status transition attempted.

    Chunk status must follow this state machine:
    PENDING → EMBEDDED → INDEXED
        ↓
      FAILED

    Maps to HTTP 409 Conflict.
    """

    @override
    def __init__(self, chunk_id: str, current_status: str, attempted_transition: str) -> None:
        """Initialize invalid status transition exception.

        Args:
            chunk_id: ID of the chunk
            current_status: Current status of the chunk
            attempted_transition: The transition that was attempted

        """
        super().__init__(
            f"Cannot {attempted_transition} chunk {chunk_id} in {current_status} status. "
            f"Valid transitions: PENDING→EMBEDDED→INDEXED or PENDING→FAILED"
        )
        self.chunk_id = chunk_id
        self.current_status = current_status
        self.attempted_transition = attempted_transition


@final
class ChunkAlreadyEmbeddedError(ConflictException):
    """Chunk already has an embedding (1:1 invariant violation).

    Each chunk should have exactly one embedding. To re-embed a chunk,
    the existing embedding must be deleted first.

    Maps to HTTP 409 Conflict.
    """

    @override
    def __init__(self, chunk_id: str, existing_embedding_id: str) -> None:
        """Initialize chunk already embedded exception.

        Args:
            chunk_id: ID of the chunk
            existing_embedding_id: ID of the existing embedding

        """
        super().__init__(
            f"Chunk {chunk_id} already has embedding {existing_embedding_id}. "
            f"Each chunk can have exactly one embedding (1:1 invariant)."
        )
        self.chunk_id = chunk_id
        self.existing_embedding_id = existing_embedding_id


@final
class DuplicateModalityError(ConflictException):
    """Multiple strategies for same modality in config.

    A vectorization config cannot have multiple chunking strategies
    for the same modality type.

    Maps to HTTP 409 Conflict.
    """

    @override
    def __init__(self, modality: str) -> None:
        """Initialize duplicate modality error.

        Args:
            modality: The modality type that has duplicate strategies

        """
        super().__init__(f"Cannot have multiple chunking strategies for {modality} modality in same config")
        self.modality = modality
