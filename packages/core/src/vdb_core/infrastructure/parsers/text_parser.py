"""Text parser for plain text documents."""

from typing import override

from vdb_core.domain.entities import DocumentFragment
from vdb_core.domain.entities.extracted_content import ExtractedContent
from vdb_core.domain.services import IParser
from vdb_core.domain.value_objects import ModalityType


class TextParser(IParser):
    """Parser for plain text files (UTF-8 encoded)."""

    @override
    async def parse(self, fragment: DocumentFragment) -> list[ExtractedContent]:
        """Parse text fragment by decoding UTF-8.

        Args:
            fragment: Raw fragment with UTF-8 encoded bytes

        Returns:
            Single ExtractedContent with TEXT modality

        Raises:
            ValueError: If content is not valid UTF-8

        """
        try:
            # Decode UTF-8
            decoded_text = fragment.content.decode("utf-8")
        except UnicodeDecodeError as e:
            msg = f"Failed to decode fragment {fragment.id} as UTF-8: {e}"
            raise ValueError(msg) from e

        # Create ExtractedContent
        return [
            ExtractedContent(
                document_id=fragment.document_id,
                document_fragment_id=fragment.id,
                content=decoded_text.encode("utf-8"),  # Store as bytes
                modality=ModalityType.TEXT,
                modality_sequence_number=fragment.sequence_number + 1,  # Convert from 0-indexed to 1-indexed
                is_last_of_modality=fragment.is_last_fragment,
                metadata={"encoding": "utf-8"},
            )
        ]

    @override
    def can_parse(self, content_type: str) -> bool:
        """Check if content type is plain text."""
        return content_type in self.supported_content_types

    @property
    @override
    def supported_content_types(self) -> frozenset[str]:
        """Supported text MIME types."""
        return frozenset(
            {
                "text/plain",
                "text/markdown",
                "text/csv",
                "text/html",
                "text/xml",
                "application/json",
            }
        )
