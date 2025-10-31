"""ExtractedContent - parsed content from DocumentFragment ready for chunking."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from pydantic.dataclasses import dataclass

if TYPE_CHECKING:
    from vdb_core.domain.value_objects.strategy import ModalityType

    from .document_fragment_id import DocumentFragmentId


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractedContent:
    """Extracted content from a DocumentFragment after parsing.

    Represents content that has been:
    1. Uploaded as DocumentFragment (raw bytes)
    2. Parsed by modality detector (modality identified)
    3. Ready to be routed to appropriate ChunkingStrategy

    Tracks source fragments and document offsets to enable:
    - Tracing chunks back to their source fragments
    - Supporting extraction that spans multiple fragments
    - Debugging and auditing of the extraction process

    Attributes:
        content: The parsed content (bytes)
        modality: The detected modality type (TEXT, IMAGE, VIDEO, AUDIO)
        source_fragments: List of (fragment_id, start_offset, end_offset) tuples tracking which
                         fragments this content came from. Supports multi-fragment extraction.
        document_offset_start: Global byte position where this content starts in reassembled document
        document_offset_end: Global byte position where this content ends in reassembled document
        metadata: Optional metadata from parsing (e.g., {"width": 1920, "height": 1080})

    Example:
        # TEXT content from a single fragment
        text_content = ExtractedContent(
            content=b"This is a document about AI...",
            modality=ModalityType(ModalityTypeEnum.TEXT),
            source_fragments=[(fragment_id, 0, 100)],
            document_offset_start=0,
            document_offset_end=100,
            metadata={"encoding": "utf-8", "language": "en", "page": 1}
        )

        # IMAGE content extracted from PDF
        image_content = ExtractedContent(
            content=image_bytes,
            modality=ModalityType(ModalityTypeEnum.IMAGE),
            source_fragments=[(fragment_id, 1500, 2000)],
            document_offset_start=1500,
            document_offset_end=2000,
            metadata={"width": 1920, "height": 1080, "format": "JPEG", "page": 2}
        )

        # Content spanning multiple fragments
        multipart_content = ExtractedContent(
            content=combined_bytes,
            modality=ModalityType(ModalityTypeEnum.TEXT),
            source_fragments=[
                (fragment_id_1, 800, 1024),  # Last 224 bytes of fragment 1
                (fragment_id_2, 0, 500),      # First 500 bytes of fragment 2
            ],
            document_offset_start=800,
            document_offset_end=1524,
            metadata={"spans_fragments": True}
        )

    """

    content: bytes
    modality: ModalityType
    source_fragments: list[tuple[DocumentFragmentId, int, int]]  # (fragment_id, start, end)
    document_offset_start: int  # Global position in reassembled document
    document_offset_end: int  # Global position in reassembled document
    metadata: dict[str, object] | None = None

    def __post_init__(self) -> None:
        """Validate extracted content."""
        if not isinstance(self.content, bytes):
            msg = f"content must be bytes, got {type(self.content)}"
            raise TypeError(msg)

        if not self.content:
            msg = "content cannot be empty"
            raise ValueError(msg)

        if not self.source_fragments:
            msg = "source_fragments cannot be empty"
            raise ValueError(msg)

        if self.document_offset_start < 0:
            msg = f"document_offset_start must be non-negative, got {self.document_offset_start}"
            raise ValueError(msg)

        if self.document_offset_end <= self.document_offset_start:
            msg = (
                f"document_offset_end ({self.document_offset_end}) must be > "
                f"document_offset_start ({self.document_offset_start})"
            )
            raise ValueError(msg)

        # Validate fragment offsets
        for i, (_frag_id, start, end) in enumerate(self.source_fragments):
            if start < 0:
                msg = f"Fragment {i}: start offset must be non-negative, got {start}"
                raise ValueError(msg)
            if end <= start:
                msg = f"Fragment {i}: end ({end}) must be > start ({start})"
                raise ValueError(msg)

    @property
    def size_bytes(self) -> int:
        """Get content size in bytes."""
        return len(self.content)

    def get_metadata(self, key: str, default: object = None) -> object:
        """Get metadata value by key.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default

        """
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)
