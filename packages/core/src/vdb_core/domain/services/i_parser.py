"""Parser protocol for extracting content from document fragments.

Parsers convert raw bytes (PDF, DOCX, images, etc.) into ExtractedContent
value objects with detected modality and metadata.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vdb_core.domain.entities import DocumentFragment
    from vdb_core.domain.entities.extracted_content import ExtractedContent


class IParser(ABC):
    """Protocol for parsing document fragments into structured content.

    Each parser handles specific file formats and extracts content with
    modality information. A single fragment can produce multiple ExtractedContent
    objects (e.g., PDF with text + images).

    Implementations:
    - TextParser: Plain text, UTF-8 decoding
    - PDFParser: Extract text and images from PDF
    - DOCXParser: Extract text and images from Word docs
    - ImageParser: Process images (JPEG, PNG, WebP)
    - AudioParser: Process audio files
    - VideoParser: Extract frames and audio from video
    """

    @abstractmethod
    async def parse(self, fragment: DocumentFragment) -> list[ExtractedContent]:
        """Parse a document fragment into extracted content.

        Args:
            fragment: Raw document fragment with bytes

        Returns:
            List of ExtractedContent objects, one per modality found.
            For example, a PDF fragment might return:
            [
                ExtractedContent(modality=TEXT, content=b"..."),
                ExtractedContent(modality=IMAGE, content=b"..."),
            ]

        Raises:
            ValueError: If fragment cannot be parsed

        """

    @abstractmethod
    def can_parse(self, content_type: str) -> bool:
        """Check if this parser can handle the given content type.

        Args:
            content_type: MIME type (e.g., "application/pdf", "text/plain")

        Returns:
            True if this parser supports the content type

        """

    @property
    @abstractmethod
    def supported_content_types(self) -> frozenset[str]:
        """Get MIME types this parser supports."""
