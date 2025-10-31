"""Passthrough chunking strategy - no chunking applied."""

from __future__ import annotations

from vdb_core.domain.value_objects import ModalityType


class PassthroughChunker:
    """Passthrough chunker that returns content as-is without splitting.

    Used for:
    - Images: Should not be split (pass entire image to embedding model)
    - Audio: Should not be split (pass entire audio to embedding model)
    - Video: Should not be split (pass entire video to embedding model)
    - Small documents: When chunking isn't needed

    For multimodal embeddings (e.g., CLIP, Cohere multimodal):
    - TEXT uses SentenceSplitChunker → breaks into chunks
    - IMAGE uses PassthroughChunker → keeps whole image
    - Both go to same multimodal embedding model
    """

    def __init__(self, config: dict[str, object] | None = None) -> None:
        """Initialize passthrough chunker.

        Args:
            config: Configuration dict (ignored, passthrough has no config)

        """
        self.config = config or {}

    @property
    def identifier(self) -> str:
        """Return strategy identifier."""
        return "passthrough"

    @property
    def max_output_tokens(self) -> int | None:
        """Return max output token limit (None = no limit)."""
        return None

    @property
    def supported_modalities(self) -> frozenset[ModalityType]:
        """Return supported modalities (IMAGE, TEXT)."""
        return frozenset([
            ModalityType.IMAGE,
            ModalityType.TEXT,  # Also supports text for small docs
        ])

    def supports_modality(self, modality: ModalityType) -> bool:
        """Check if strategy supports the modality."""
        return modality in self.supported_modalities

    def chunk(self, content: str | bytes) -> list[str | bytes]:
        """Return content as-is without splitting.

        Args:
            content: Content to "chunk" (any type)

        Returns:
            List with single element (the original content)

        Raises:
            ValueError: If content is empty

        """
        if not content:
            msg = "Content cannot be empty"
            raise ValueError(msg)

        # Return content unchanged as single chunk
        return [content]
