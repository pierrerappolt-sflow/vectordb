"""PDF parser - placeholder for future implementation."""

from typing import override

from vdb_core.domain.entities import DocumentFragment
from vdb_core.domain.entities.extracted_content import ExtractedContent
from vdb_core.domain.services import IParser


class PDFParser(IParser):
    """Parser for PDF documents.

    TODO: Implement using pypdf or pdfplumber to extract:
    - Text content (pages, paragraphs)
    - Embedded images
    - Metadata (author, title, etc.)

    Will produce multiple ExtractedContent objects:
    - One for TEXT modality (extracted text)
    - One for each embedded IMAGE
    """

    @override
    async def parse(self, fragment: DocumentFragment) -> list[ExtractedContent]:
        """Parse PDF fragment.

        TODO: Implement PDF parsing using library like pypdf/pdfplumber.

        Args:
            fragment: Raw fragment with PDF bytes

        Returns:
            List of ExtractedContent (text + images)

        Raises:
            NotImplementedError: PDF parsing not yet implemented

        """
        msg = "PDF parsing not yet implemented. Install pypdf/pdfplumber and implement extraction logic."
        raise NotImplementedError(msg)

    @override
    def can_parse(self, content_type: str) -> bool:
        """Check if content type is PDF."""
        return content_type in self.supported_content_types

    @property
    @override
    def supported_content_types(self) -> frozenset[str]:
        """Supported PDF MIME types."""
        return frozenset({"application/pdf"})
