"""ExtractedContent - parsed content from DocumentFragment ready for chunking."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from vdb_core.domain.base import IEntity
from vdb_core.domain.value_objects import (
    DocumentFragmentId,
    DocumentId,
    ExtractedContentId,
        ExtractedContentStatus,
    ModalityType,
)
from vdb_core.utils.dt_utils import utc_now


@dataclass(slots=True, kw_only=True, eq=False)
class ExtractedContent(IEntity):
    """Parsed content from DocumentFragment, ready for chunking.

    Represents intermediate stage between raw upload and chunks:
    1. DocumentFragment: Raw bytes (no modality)
    2. ExtractedContent: Parsed content with modality.

    TODO: This needs better typing, or some narrowing
    of type based on the modality, but:

    The goal here is to make document fragmentation as fast as possible (UX reasons),
    then have ExtractedContent represent modality-specific content from the Document,
    that can be routed to a modality-specific chunking strategy.
    At chunk-time, the chunking strategy can grab the previous or next ExtractedContent
    of the same modality to create a complete chunk.

    Attributes:
        id: Unique identifier
        document_id: Document this content belongs to
        document_fragment_id: Source fragment
        content: Parsed content (bytes)
        modality: Detected modality (TEXT, IMAGE, VIDEO, AUDIO)
        modality_sequence_number: Order within modality (1st TEXT, 2nd TEXT, etc.)
        is_last_of_modality: True if this is the last content of this modality for document
        status: Processing status (PENDING, CHUNKED, FAILED)
        metadata: Optional metadata from parsing

    Invariants:
        - modality_sequence_number starts at 1 and is consecutive per (document_id, modality)
        - Exactly ONE ExtractedContent with is_last_of_modality=True per (document_id, modality)
        - Content cannot be empty

    Example:
        # First TEXT content from PDF page 1
        text_1 = ExtractedContent(
            document_id=doc.id,
            document_fragment_id=fragment_1.id,
            content=b"This is page 1 text...",
            modality=ModalityType.TEXT,
            modality_sequence_number=1,
            is_last_of_modality=False,
            metadata={"page": 1, "encoding": "utf-8"}
        )

        # Second TEXT content from PDF page 2
        text_2 = ExtractedContent(
            document_id=doc.id,
            document_fragment_id=fragment_1.id,
            content=b"This is page 2 text...",
            modality=ModalityType.TEXT,
            modality_sequence_number=2,
            is_last_of_modality=False,
            metadata={"page": 2}
        )

        # Last TEXT content from final fragment
        text_final = ExtractedContent(
            document_id=doc.id,
            document_fragment_id=fragment_3.id,
            content=b"Final page text...",
            modality=ModalityType.TEXT,
            modality_sequence_number=10,
            is_last_of_modality=True,
            metadata={"page": 10}
        )

    """

    id: ExtractedContentId = field(default_factory=uuid4, init=False)

    document_id: DocumentId
    document_fragment_id: DocumentFragmentId
    content: bytes
    modality: ModalityType
    modality_sequence_number: int
    is_last_of_modality: bool = False
    # TODO (PR): Remove this and make it value obejct
    status: ExtractedContentStatus = field(default=ExtractedContentStatus.PENDING, init=False)
    metadata: dict[str, object] | None = None

    _mutable_fields: frozenset[str] = frozenset({"status", "metadata"})

    def __post_init__(self) -> None:
        """Validate extracted content invariants."""
        if not self.content:
            msg = "content cannot be empty"
            raise ValueError(msg)

        if not isinstance(self.content, bytes):
            msg = f"content must be bytes, got {type(self.content)}"
            raise TypeError(msg)

        if self.modality_sequence_number < 1:
            msg = f"modality_sequence_number must be >= 1, got {self.modality_sequence_number}"
            raise ValueError(msg)

        IEntity.__post_init__(self)

    def mark_failed(self, reason: str) -> None:
        """Mark as failed with reason."""
        if not reason or not reason.strip():
            msg = "failure reason cannot be empty"
            raise ValueError(msg)

        object.__setattr__(self, "status", ExtractedContentStatus.FAILED)

        # Store failure reason in metadata, for debugging purposes.
        metadata = self.metadata or {}
        metadata["failure_reason"] = reason
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "updated_at", utc_now())

    @property
    def size_bytes(self) -> int:
        """Get content size in bytes."""
        return len(self.content)
