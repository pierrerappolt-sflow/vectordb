"""Document entity - part of Library aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4

from vdb_core.domain.base import IEntity, LazyCollection
from vdb_core.domain.events.document_events import DocumentFragmentReceived
from vdb_core.domain.value_objects import (
    ChunkId,
    ContentHash,
    DocumentFragmentId,
    DocumentId,
    DocumentName,
    ExtractedContentId,
    LibraryId,
)
from vdb_core.domain.value_objects.document.document_status import DocumentStatus

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from vdb_core.domain.entities.extracted_content import ExtractedContent

    from vdb_core.domain.value_objects.chunk import Chunk
    from .document_fragment import DocumentFragment


@dataclass(kw_only=True, eq=False)
class Document(IEntity):
    """Document entity - part of Library aggregate.

    Following DDD principles:
    - Part of the Library aggregate (accessed through Library → Document)
    - Read-only access to chunk sets via lazy loading
    - Document processing happens through background pipelines

    Documents are never loaded entirely into memory. Content is streamed
    as DocumentSegments, with modality detection and routing happening
    at processing time.

    Uses lazy loading for chunk sets to avoid loading all chunking strategies at once.

    DDD invariant protection:
    - All fields are immutable from outside
    - Mutations must go through entity methods
    - Methods use object.__setattr__ internally
    """

    id: DocumentId = field(default_factory=uuid4, init=False)
    library_id: LibraryId
    name: DocumentName
    status: str = "pending"
    upload_complete: bool = field(default=False, init=False)

    # Define which fields can be updated via update() method
    _mutable_fields: frozenset[str] = frozenset({"name", "status"})

    # Lazy loaded children entities
    _fragments: LazyCollection[DocumentFragment, DocumentFragmentId] = field(
        default_factory=lambda: LazyCollection(), init=False, repr=False
    )
    _extracted_contents: dict[ExtractedContentId, ExtractedContent] = field(
        default_factory=dict, init=False, repr=False
    )
    _chunks: dict[ChunkId, Chunk] = field(default_factory=dict, init=False, repr=False)
    _chunk_loader: Callable[[], AsyncIterator[Chunk]] | None = field(default=None, init=False, repr=False)

    def add_fragment(
        self,
        sequence_number: int,
        content: bytes,
        content_hash: ContentHash,
        is_final: bool = False,  # noqa: FBT002
    ) -> DocumentFragment:
        """Add a fragment to this document during streaming upload.

        Following Cosmic Python pattern:
        - Creates DocumentFragment entity
        - Adds DocumentFragmentReceived event as side effect
        - Tracks fragment in document
        - Updates document's updated_at timestamp

        Args:
            sequence_number: Order fragment was received (0-indexed)
            content: Raw bytes (could be part of PDF, DOCX, image, video, etc.)
            content_hash: Hash for deduplication and verification
            is_final: True if this is the last fragment

        Returns:
            The newly created fragment

        Note:
            Fragments contain raw bytes only - no modality yet.
            Modality is determined during parsing phase when fragments are processed.

        Example:
            fragment = document.add_fragment(
                sequence_number=0,
                content=b"...",  # Raw bytes from PDF, DOCX, etc.
                content_hash=ContentHash(...),
                is_final=False
            )
            # document.events contains DocumentFragmentReceived event

        """
        from vdb_core.utils.dt_utils import utc_now

        from .document_fragment import DocumentFragment

        fragment = DocumentFragment(
            document_id=self.id,
            sequence_number=sequence_number,
            content=content,
            content_hash=content_hash,
            is_last_fragment=is_final,
        )

        # Initialize fragments collection if not set
        if self._fragments is None:
            # Create empty loader that yields nothing (fragments added locally)
            async def empty_loader():
                return
                yield  # Make it a generator
            object.__setattr__(
                self,
                "_fragments",
                LazyCollection[DocumentFragment, DocumentFragmentId](
                    loader=empty_loader,
                    get_id=lambda f: f.id,
                ),
            )

        self._fragments.add_to_cache(fragment)

        # Add event as side effect (Cosmic Python pattern)
        self.events.append(
            DocumentFragmentReceived(
                library_id=self.library_id,
                document_id=self.id,
                fragment_id=fragment.id,
                sequence_number=sequence_number,
                is_final=is_final,
            )
        )

        if is_final:
            object.__setattr__(self, "upload_complete", True)
            # Set to PROCESSING - will be updated to COMPLETED/FAILED by ParseDocumentWorkflow
            object.__setattr__(self, "status", DocumentStatus.PROCESSING)
        # Update timestamp to reflect modification
        object.__setattr__(self, "updated_at", utc_now())

        return fragment

    @property
    def fragments(self) -> tuple[DocumentFragment, ...]:
        """Get cached fragments ordered by sequence number (does not trigger lazy loading).

        Fragments are sorted by sequence_number to ensure correct reconstruction
        of the original document content.

        Returns read-only view of cached fragments.
        Use add_fragment() to add fragments, or load_fragments() to lazy load all.
        """
        if self._fragments is None:
            return tuple()
        return tuple(sorted(self._fragments.cached_items, key=lambda f: f.sequence_number))

    async def get_fragment(self, fragment_id: DocumentFragmentId) -> DocumentFragment:
        """Get a specific fragment by ID (lazy loads if not cached).

        Args:
            fragment_id: ID of the fragment to retrieve

        Returns:
            The requested fragment

        Raises:
            RuntimeError: If no fragment loader is configured
            KeyError: If fragment is not found

        """
        if self._fragments is None:
            msg = "No fragments loaded for this document"
            raise KeyError(msg)
        return await self._fragments.get(fragment_id)

    async def load_fragments(self) -> AsyncIterator[DocumentFragment]:
        """Lazy load all fragments for this document.

        First yields any cached fragments, then lazy loads remaining fragments.

        Yields:
            Document fragments ordered by sequence number

        Raises:
            RuntimeError: If no fragment loader is configured

        """
        if self._fragments is None:
            msg = "No fragment loader configured for this document"
            raise RuntimeError(msg)
        async for fragment in self._fragments.all():
            yield fragment

    def add_extracted_content(self, extracted_content: ExtractedContent) -> None:
        """Add extracted content to this document after parsing.

        Note: This method does NOT publish events. Events should only be published
        by the aggregate root (Library) via Library.add_document_extracted_content().

        Args:
            extracted_content: The extracted content to add

        """
        from vdb_core.utils.dt_utils import utc_now

        # Store extracted content
        self._extracted_contents[extracted_content.id] = extracted_content

        # Update timestamp to reflect modification
        object.__setattr__(self, "updated_at", utc_now())


    @property
    def chunks(self) -> list[Chunk]:
        """Get all cached chunks in this document.

        Returns read-only view to prevent external modification.
        Use add_chunk() to add chunks.
        For lazy loading all chunks, use load_chunks().
        """
        return list(self._chunks.values())

    async def load_chunks(self) -> AsyncIterator[Chunk]:
        """Lazy load chunks for this document.

        First yields any cached chunks, then lazy loads remaining chunks.

        Raises:
            RuntimeError: If no chunk loader is configured.

        """
        # First yield any cached chunks
        for chunk in self._chunks.values():
            yield chunk

        # Then lazy load remaining chunks
        if not self._chunk_loader:
            msg = "No chunk loader configured for this document"
            raise RuntimeError(msg)

        async for chunk in self._chunk_loader():
            if chunk.id not in self._chunks:
                self._chunks[chunk.id] = chunk
                yield chunk
