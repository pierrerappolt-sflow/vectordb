"""Entity not found exceptions (HTTP 404)."""

from typing import ClassVar, final

from vdb_core.domain.base import DomainException


class EntityNotFoundError(DomainException):
    """Base exception for entity not found errors (HTTP 404).

    Raised when attempting to access a resource that doesn't exist.

    Maps to HTTP 404 Not Found.

    Subclasses should define entity_type as a ClassVar.
    """

    entity_type: ClassVar[str] = "Entity"

    def __init__(self, entity_id: str) -> None:
        """Initialize with entity ID.

        Args:
            entity_id: The ID of the entity that was not found

        """
        self.entity_id = entity_id
        super().__init__(f"{self.entity_type} with id '{entity_id}' not found")


@final
class LibraryNotFoundError(EntityNotFoundError):
    """Library not found."""

    entity_type: ClassVar[str] = "Library"


@final
class DocumentNotFoundError(EntityNotFoundError):
    """Document not found."""

    entity_type: ClassVar[str] = "Document"


@final
class ChunkNotFoundError(EntityNotFoundError):
    """Chunk not found."""

    entity_type: ClassVar[str] = "Chunk"


@final
class EmbeddingNotFoundError(EntityNotFoundError):
    """Embedding not found."""

    entity_type: ClassVar[str] = "Embedding"


@final
class ChunkingStrategyNotFoundError(EntityNotFoundError):
    """ChunkingStrategy not found."""

    entity_type: ClassVar[str] = "ChunkingStrategy"


@final
class EmbeddingStrategyNotFoundError(EntityNotFoundError):
    """EmbeddingStrategy not found."""

    entity_type: ClassVar[str] = "EmbeddingStrategy"


@final
class VectorizationConfigNotFoundError(EntityNotFoundError):
    """VectorizationConfig not found."""

    entity_type: ClassVar[str] = "VectorizationConfig"
