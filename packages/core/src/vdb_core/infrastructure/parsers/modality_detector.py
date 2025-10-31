"""Modality detector implementation using magic bytes."""

import mimetypes
from collections.abc import AsyncIterator
from typing import override

from vdb_core.domain.services import IModalityDetector
from vdb_core.domain.value_objects import ExtractedContent, ModalityType


class ModalityDetector(IModalityDetector):
    """Detect content modality from raw bytes using magic bytes and MIME types.

    Uses file magic bytes (first few bytes) to identify file type, then
    maps to modality categories (TEXT, IMAGE, AUDIO, VIDEO).
    """

    # Magic bytes for common file types
    MAGIC_BYTES = {
        # PDF
        b"%PDF": ModalityType.TEXT,
        # Images
        b"\x89PNG": ModalityType.IMAGE,
        b"\xff\xd8\xff": ModalityType.IMAGE,  # JPEG
        b"GIF87a": ModalityType.IMAGE,
        b"GIF89a": ModalityType.IMAGE,
        b"RIFF": ModalityType.IMAGE,  # WebP (also used for WAV, need more checks)
        # Documents
        b"PK\x03\x04": ModalityType.TEXT,  # ZIP-based (DOCX, XLSX, etc.)
    }

    @override
    def detect(self, content: bytes, filename: str | None = None) -> ModalityType:
        """Detect modality from raw bytes and optional filename.

        Args:
            content: Raw bytes to analyze
            filename: Optional filename for extension-based detection

        Returns:
            Detected modality type

        Raises:
            ValueError: If modality cannot be determined

        """
        if not content:
            msg = "Cannot detect modality from empty content"
            raise ValueError(msg)

        # Try magic bytes first (more reliable)
        modality = self._detect_from_magic_bytes(content)
        if modality:
            return modality

        # Fall back to filename extension
        if filename:
            modality = self._detect_from_filename(filename)
            if modality:
                return modality

        # Default to TEXT if nothing else matches
        # Attempt UTF-8 decode to verify
        try:
            content[:1000].decode("utf-8")
            return ModalityType.TEXT
        except UnicodeDecodeError:
            msg = f"Cannot determine modality for content (first bytes: {content[:20].hex()})"
            raise ValueError(msg)

    def _detect_from_magic_bytes(self, content: bytes) -> ModalityType | None:
        """Detect modality from magic bytes."""
        for magic, modality in self.MAGIC_BYTES.items():
            if content.startswith(magic):
                # Special case: RIFF can be WebP (image) or other formats
                if magic == b"RIFF" and len(content) > 12:
                    if content[8:12] == b"WEBP":
                        return ModalityType.IMAGE
                    # Skip non-WebP RIFF files
                    continue
                return modality
        return None

    def _detect_from_filename(self, filename: str) -> ModalityType | None:
        """Detect modality from file extension."""
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            return None

        if mime_type.startswith("text/"):
            return ModalityType.TEXT
        if mime_type in ("application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument"):
            return ModalityType.TEXT
        if mime_type.startswith("image/"):
            return ModalityType.IMAGE

        return None

    @override
    def detect_mime_type(self, content: bytes, filename: str | None = None) -> str:
        """Detect MIME type from content.

        Args:
            content: Raw bytes to analyze
            filename: Optional filename hint

        Returns:
            MIME type string (e.g., "application/pdf")

        """
        # Try filename first for better accuracy
        if filename:
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                return mime_type

        # Fall back to magic bytes
        if content.startswith(b"%PDF"):
            return "application/pdf"
        if content.startswith(b"\x89PNG"):
            return "image/png"
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"GIF8"):
            return "image/gif"
        if content.startswith(b"RIFF") and len(content) > 12 and content[8:12] == b"WEBP":
            return "image/webp"
        if content.startswith(b"PK\x03\x04"):
            # ZIP-based, could be DOCX, XLSX, etc.
            return "application/zip"
        if content.startswith((b"ID3", b"\xff\xfb")):
            return "audio/mpeg"
        if content.startswith(b"\x00\x00\x00 ftyp"):
            return "video/mp4"

        # Default to octet-stream
        return "application/octet-stream"

    @override
    async def detect_and_segment(
        self,
        document_content: bytes,
    ) -> AsyncIterator[ExtractedContent]:
        """Detect modalities and yield processable segments.

        For basic implementation, yields entire content as single segment.
        More advanced implementations could chunk large documents or
        extract multiple modalities from multi-modal content.

        Args:
            document_content: Raw document bytes

        Yields:
            Single ExtractedContent with detected modality

        """
        # Detect modality for entire content
        modality = self.detect(document_content)

        # Yield entire content as single segment
        # More sophisticated implementations could:
        # - Chunk large documents into smaller segments
        # - Extract different modalities from multi-modal content (e.g., PDF with images)
        yield ExtractedContent(
            content=document_content,
            modality=modality,
            source_fragments=[],  # No fragment tracking at this level
            document_offset_start=0,
            document_offset_end=len(document_content),
            metadata={
                "mime_type": self.detect_mime_type(document_content),
            },
        )
