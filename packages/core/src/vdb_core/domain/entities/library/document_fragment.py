"""DocumentFragment entity - a piece of a document received during streaming upload."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import uuid4

from vdb_core.domain.base import IEntity
from vdb_core.domain.exceptions import DocumentTooLargeError
from vdb_core.domain.value_objects import (
    MAX_FRAGMENT_SIZE_BYTES,
    ContentHash,
    DocumentFragmentId,
    DocumentId,
)


@dataclass(kw_only=True, eq=False)
class DocumentFragment(IEntity):
    """A fragment of document content received during streaming upload.

    Fragments are <= 100MB chunks that enable streaming document processing:
    - Documents are uploaded in small fragments to avoid memory issues
    - Ingestion pipeline can process fragments before upload completes
    - Events are emitted per fragment to trigger batch processing
    - Fragments are ordered by sequence_number for content reconstruction

    Following DDD principles:
    - Part of the Library aggregate (accessed through Library → Document → Fragment)
    - Immutable once created (all mutations blocked after initialization)
    - Stores RAW BYTES ONLY - no modality yet (modality determined during parsing)
    - Each fragment emits DocumentFragmentReceived event for async processing

    IMPORTANT: Fragments contain raw bytes from the uploaded file (PDF, DOCX, image, etc.)
    Modality is NOT known at fragment creation time. The processing flow is:

    1. Upload: Create DocumentFragments (raw bytes, no modality) - API handles fragmentation
    2. Parse: Parser extracts ExtractedContent with modality (Phase 1: Ingestion)
    3. Chunk: Chunker (by modality) creates Chunks (Phase 2: Vectorization)
    4. Embed: Embedding model (by modality) creates Embeddings (Phase 2: Vectorization)

    For compound files (PDF with text + images), a single fragment can contain
    mixed content types interleaved. The parser extracts separate TEXT and IMAGE
    ExtractedContent entities from the same fragment bytes.

    Attributes:
        sequence_number: Order within document (1, 2, 3...)
        is_last_fragment: True only for the final fragment (EOF marker)
        content: Raw bytes (max 100MB enforced)
        content_hash: SHA-256 hash for deduplication/integrity

    Invariants:
        - sequence_number must be consecutive (1, 2, 3...) per document
        - Exactly ONE fragment with is_last_fragment=True per document
        - content size <= MAX_FRAGMENT_SIZE_BYTES (100MB)

    """

    id: DocumentFragmentId = field(default_factory=uuid4, init=False)
    document_id: DocumentId
    sequence_number: int  # 1, 2, 3... (consecutive)
    content: bytes  # Raw bytes - could be part of PDF, DOCX, image, video, etc.
    content_hash: ContentHash
    is_last_fragment: bool = False  # True only for final fragment (EOF)

    # DocumentFragments are immutable once created
    _mutable_fields: frozenset[str] = frozenset()

    @override
    def __post_init__(self) -> None:
        """Validate fragment invariants."""
        if self.sequence_number < 0:
            msg = f"sequence_number must be >= 0, got {self.sequence_number}"
            raise ValueError(msg)

        if not self.content:
            msg = "content cannot be empty"
            raise ValueError(msg)

        if len(self.content) > MAX_FRAGMENT_SIZE_BYTES:
            raise DocumentTooLargeError(
                size_bytes=len(self.content),
                max_size_bytes=MAX_FRAGMENT_SIZE_BYTES,
                fragment_id=str(self.id) if hasattr(self, "id") else None,
            )

        # Lock down setattr
        IEntity.__post_init__(self)

    @property
    def size_bytes(self) -> int:
        """Get the size of this fragment in bytes."""
        return len(self.content)
