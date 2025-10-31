"""Validation exceptions (HTTP 400/422)."""

from typing import final, override

from vdb_core.domain.base import DomainException


class ValidationException(DomainException):
    """Base exception for validation failures (HTTP 400/422).

    Raised when input data fails validation:
    - Invalid value object construction
    - Business rule violations during entity creation
    - Data constraints violations
    - Invalid parameters

    Maps to HTTP 400 Bad Request or 422 Unprocessable Entity.
    """

    def __init__(self, message: str) -> None:
        """Initialize validation exception.

        Args:
            message: Description of the validation failure

        """
        super().__init__(message)


@final
class ChunkTooLongError(ValidationException):
    """Chunk content exceeds embedding model's context window.

    Maps to HTTP 422 Unprocessable Entity.
    """

    @override
    def __init__(
        self,
        chunk_id: str,
        actual_tokens: int,
        max_tokens: int,
        embedding_strategy: str,
    ) -> None:
        """Initialize chunk too long exception.

        Args:
            chunk_id: ID of the chunk that is too long
            actual_tokens: Number of tokens in the chunk
            max_tokens: Maximum tokens supported by embedding model
            embedding_strategy: Name of the embedding strategy with the limit

        """
        super().__init__(
            f"Chunk {chunk_id} has {actual_tokens} tokens, exceeding "
            f"{embedding_strategy}'s maximum of {max_tokens} tokens"
        )
        self.chunk_id = chunk_id
        self.actual_tokens = actual_tokens
        self.max_tokens = max_tokens
        self.embedding_strategy = embedding_strategy


@final
class DocumentTooLargeError(ValidationException):
    """Document exceeds maximum size limit.

    Maps to HTTP 413 Payload Too Large.
    """

    @override
    def __init__(
        self,
        size_bytes: int,
        max_size_bytes: int,
        fragment_id: str | None = None,
        document_id: str | None = None,
    ) -> None:
        """Initialize document too large error.

        Args:
            size_bytes: Actual document/fragment size in bytes
            max_size_bytes: Maximum allowed size in bytes
            fragment_id: Optional fragment ID for context
            document_id: Optional document ID for context

        """
        size_mb = size_bytes / (1024 * 1024)
        max_mb = max_size_bytes / (1024 * 1024)

        msg = (
            f"Document exceeds maximum size limit: {size_mb:.2f}MB > {max_mb:.2f}MB. "
            f"Maximum document size is {max_mb:.0f}MB."
        )

        if document_id:
            msg += f" (Document: {document_id})"
        if fragment_id:
            msg += f" (Fragment: {fragment_id})"

        super().__init__(msg)
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes
        self.fragment_id = fragment_id
        self.document_id = document_id


@final
class UnsupportedModalityError(ValidationException):
    """Modality type is not supported by the library or pipeline.

    Maps to HTTP 422 Unprocessable Entity.
    """

    @override
    def __init__(self, modality_type: str, supported_modality: str) -> None:
        """Initialize unsupported modality error.

        Args:
            modality_type: The unsupported modality type that was attempted
            supported_modality: The modality type that is actually supported

        """
        super().__init__(f"Modality type '{modality_type}' is not supported. Only '{supported_modality}' is supported.")
        self.modality_type = modality_type
        self.supported_modality = supported_modality
