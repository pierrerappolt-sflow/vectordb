"""Composite parser that routes to appropriate parser based on content type."""

from typing import override

from vdb_core.domain.entities import DocumentFragment
from vdb_core.domain.entities.extracted_content import ExtractedContent
from vdb_core.domain.services import IModalityDetector, IParser


class CompositeParser(IParser):
    """Parser that routes fragments to appropriate parser based on MIME type.

    Uses modality detector to determine content type, then delegates to
    specialized parsers (TextParser, PDFParser, etc.).

    Example:
        detector = ModalityDetector()
        composite = CompositeParser(
            modality_detector=detector,
            parsers=[TextParser(), PDFParser()]
        )
        results = await composite.parse(fragment)

    """

    def __init__(
        self,
        modality_detector: IModalityDetector,
        parsers: list[IParser],
    ) -> None:
        """Initialize composite parser with parsers.

        Args:
            modality_detector: Service for detecting MIME type
            parsers: List of specialized parsers to route to

        """
        self._modality_detector = modality_detector
        self._parsers = parsers
        self._parser_map = self._build_parser_map(parsers)

    def _build_parser_map(self, parsers: list[IParser]) -> dict[str, IParser]:
        """Build MIME type -> parser mapping.

        Args:
            parsers: List of parsers

        Returns:
            Dictionary mapping MIME types to parsers

        """
        parser_map: dict[str, IParser] = {}
        for parser in parsers:
            for content_type in parser.supported_content_types:
                parser_map[content_type] = parser
        return parser_map

    @override
    async def parse(self, fragment: DocumentFragment) -> list[ExtractedContent]:
        """Parse fragment by routing to appropriate parser.

        Args:
            fragment: Document fragment to parse

        Returns:
            List of ExtractedContent from the delegated parser

        Raises:
            ValueError: If no parser supports the detected content type

        """
        # Detect MIME type
        mime_type = self._modality_detector.detect_mime_type(
            content=fragment.content,
            filename=None,  # Could enhance to pass document name if available
        )

        # Find appropriate parser
        parser = self._parser_map.get(mime_type)
        if not parser:
            # Try wildcard matching (e.g., "text/*" for "text/plain")
            for content_type, p in self._parser_map.items():
                if "/" in content_type:
                    category, _ = content_type.split("/", 1)
                    if mime_type.startswith(f"{category}/"):
                        parser = p
                        break

        if not parser:
            msg = (
                f"No parser available for content type '{mime_type}'. "
                f"Supported types: {sorted(self._parser_map.keys())}"
            )
            raise ValueError(msg)

        # Delegate to specialized parser
        return await parser.parse(fragment)

    @override
    def can_parse(self, content_type: str) -> bool:
        """Check if any registered parser supports this content type.

        Args:
            content_type: MIME type to check

        Returns:
            True if a parser is registered for this type

        """
        return content_type in self._parser_map

    @property
    @override
    def supported_content_types(self) -> frozenset[str]:
        """Get all supported MIME types from registered parsers.

        Returns:
            Frozen set of all MIME types supported by any parser

        """
        return frozenset(self._parser_map.keys())
