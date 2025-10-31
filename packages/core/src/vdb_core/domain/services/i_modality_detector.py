"""IModalityDetector interface - detects modalities in document content."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from vdb_core.domain.value_objects import ExtractedContent, ModalityType


class IModalityDetector(ABC):
    """Interface for detecting modalities in document content and streaming segments.

    Implementations analyze raw document content and yield ExtractedContent
    with detected modality types. This enables:

    1. Streaming large documents without loading entire content into memory
    2. Modality detection (text, image, etc.) on document portions
    3. Routing segments to appropriate chunking strategies

    Example:
        # Infrastructure layer: TextModalityDetector (no-op)
        detector = TextModalityDetector()
        async for extracted in detector.detect_and_segment(document_bytes):
            # extracted.modality.value == ModalityType.TEXT
            # extracted.content == chunk of text bytes
            pass

    """

    @abstractmethod
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

    @abstractmethod
    def detect_mime_type(self, content: bytes, filename: str | None = None) -> str:
        """Detect MIME type from content.

        Args:
            content: Raw bytes to analyze
            filename: Optional filename hint

        Returns:
            MIME type string (e.g., "application/pdf")

        """

    @abstractmethod
    def detect_and_segment(
        self,
        document_content: bytes,
    ) -> AsyncIterator[ExtractedContent]:
        """Detect modalities and yield processable segments.

        Args:
            document_content: Raw document bytes

        Yields:
            ExtractedContent objects with detected modality and content

        Example:
            For TEXT-only documents, yields segments with ModalityType.TEXT.
            For multi-modal PDFs, might yield TEXT segments and IMAGE segments.

        Note:
            This is an async generator method. Implementations should use
            `async def detect_and_segment(...) -> AsyncIterator[...]:`
            and use `yield` to produce results.

        """
