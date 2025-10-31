"""IChunkingStrategy - domain interface for chunking implementations.

Implementations live in the infrastructure layer and are registered via DI container.
Each strategy encapsulates:
- Chunking algorithm configuration (max_size, overlap, etc.)
- Tokenization logic
- Actual content splitting logic
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from vdb_core.domain.value_objects import ModalityType


@runtime_checkable
class IChunkingStrategy(Protocol):
    """Domain interface for chunking strategy implementations.

    Concrete implementations live in infrastructure layer:
    - infrastructure/chunking/sentence_split_chunker.py
    - infrastructure/chunking/semantic_v2_chunker.py
    - infrastructure/chunking/recursive_chunker.py
    - infrastructure/chunking/fixed_chunker.py

    Each implementation:
    1. Takes configuration in __init__ (max_chunk_size, overlap, etc.)
    2. Defines metadata (supported_modalities, max_output_tokens)
    3. Implements chunk() to split content

    The domain layer works with this interface only, never with concrete types.
    """

    @property
    def identifier(self) -> str:
        """Strategy identifier for persistence.

        Returns:
            String identifier for this strategy (e.g., "sentence-split")

        Example:
            strategy = SentenceSplitChunker(max_chunk_size=512)
            assert strategy.identifier == "sentence-split"

        """
        ...

    @property
    def max_output_tokens(self) -> int | None:
        """Maximum tokens per output chunk (None if variable).

        Used to validate compatibility with embedding strategy's max_tokens.

        Returns:
            Maximum chunk size in tokens, or None for variable-size strategies

        Example:
            fixed = FixedChunker(max_chunk_size=512)
            assert fixed.max_output_tokens == 512

            sentence = SentenceSplitChunker()
            assert sentence.max_output_tokens is None  # Variable size

        """
        ...

    @property
    def supported_modalities(self) -> frozenset[ModalityType]:
        """Modality types supported by this strategy.

        Returns:
            Frozenset of supported modality types

        Example:
            text_chunker = SentenceSplitChunker()
            assert text_chunker.supported_modalities == frozenset([ModalityType.TEXT])

            # Future: Image tiling strategy
            image_chunker = ImageTileChunker(tile_size=512)
            assert ModalityType.IMAGE in image_chunker.supported_modalities

        """
        ...

    def supports_modality(self, modality: ModalityType) -> bool:
        """Check if this strategy supports the given modality.

        Args:
            modality: The modality type to check

        Returns:
            True if this strategy supports the modality, False otherwise

        Example:
            strategy = SentenceSplitChunker()
            assert strategy.supports_modality(ModalityType.TEXT) is True
            assert strategy.supports_modality(ModalityType.IMAGE) is False

        """
        ...

    def chunk(self, content: str | bytes) -> list[str | bytes]:
        """Split content into chunks.

        Args:
            content: Content to chunk (str for TEXT, bytes for IMAGE/AUDIO/VIDEO)

        Returns:
            List of chunks, each chunk same type as input content

        Raises:
            TypeError: If content type doesn't match supported modalities
            ValueError: If content is empty or invalid

        Example:
            strategy = SentenceSplitChunker(max_chunk_size=512)
            chunks = strategy.chunk("Hello world. This is a test. Another sentence.")
            assert len(chunks) >= 1
            assert all(isinstance(c, str) for c in chunks)

        """
        ...
