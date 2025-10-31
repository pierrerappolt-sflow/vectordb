"""Extracted content value object."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from pydantic.dataclasses import dataclass

if TYPE_CHECKING:
    from vdb_core.domain.value_objects.strategy import ModalityType

    from .document_fragment_id import DocumentFragmentId


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractedContent:
    """Parsed content ready for chunking."""

    content: bytes
    modality: ModalityType
    source_fragments: list[tuple[DocumentFragmentId, int, int]]
    document_offset_start: int
    document_offset_end: int
    metadata: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, bytes):
            raise TypeError(f"content must be bytes, got {type(self.content)}")
        if not self.content:
            raise ValueError("content cannot be empty")
        if not self.source_fragments:
            raise ValueError("source_fragments cannot be empty")
        if self.document_offset_start < 0:
            raise ValueError(f"document_offset_start must be non-negative, got {self.document_offset_start}")
        if self.document_offset_end <= self.document_offset_start:
            raise ValueError(
                f"document_offset_end ({self.document_offset_end}) must be > document_offset_start ({self.document_offset_start})"
            )
        for i, (_frag_id, start, end) in enumerate(self.source_fragments):
            if start < 0:
                raise ValueError(f"Fragment {i}: start offset must be non-negative, got {start}")
            if end <= start:
                raise ValueError(f"Fragment {i}: end ({end}) must be > start ({start})")

    @property
    def size_bytes(self) -> int:
        return len(self.content)

    def get_metadata(self, key: str, default: object = None) -> object:
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)
