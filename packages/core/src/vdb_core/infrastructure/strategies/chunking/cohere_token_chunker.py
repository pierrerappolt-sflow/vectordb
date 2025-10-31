"""Token-based chunker using Cohere's BPE tokenizer.

Uses Cohere SDK tokenizer in offline mode for accurate token counting:
- 512 token max for v3 models (hard limit)
- BPE (Byte-Pair Encoding) tokenization
- Chunks by tokens, not words

Tokenizer downloads model on first use, then runs offline.
"""

from __future__ import annotations

import logging

import cohere

from vdb_core.domain.value_objects import ModalityType

logger = logging.getLogger(__name__)


class CohereTokenChunker:
    """Token-based chunker for Cohere text embeddings using BPE tokenization.

    Uses Cohere SDK tokenizer for accurate token counting (not whitespace estimation).
    Handles overlap and respects Cohere's 512 token maximum.

    The tokenizer downloads on first use, then runs offline.

    Configuration:
    - chunk_size_tokens: Target chunk size (default: 256)
    - chunk_overlap_tokens: Overlap between chunks (default: 25)
    - max_tokens: Hard limit to stay within model constraints (default: 512)
    """

    def __init__(self, config: dict[str, object] | None = None) -> None:
        """Initialize Cohere token chunker.

        Args:
            config: Configuration dict from ChunkingStrategy entity.
                   Can include 'api_key' for Cohere API access.

        """
        self.config = config or {}
        chunk_size_val = self.config.get("chunk_size_tokens", 256)
        self.chunk_size: int = int(chunk_size_val) if chunk_size_val is not None else 256  # type: ignore[call-overload]
        chunk_overlap_val = self.config.get("chunk_overlap_tokens", 25)
        self.chunk_overlap: int = int(chunk_overlap_val) if chunk_overlap_val is not None else 25  # type: ignore[call-overload]
        max_tokens_val = self.config.get("max_tokens", 512)
        self.max_tokens: int = int(max_tokens_val) if max_tokens_val is not None else 512  # type: ignore[call-overload]

        # Initialize Cohere client for tokenizer access
        # Use API key from config if provided, otherwise try environment variable
        api_key_val = self.config.get("api_key")
        api_key = str(api_key_val) if api_key_val is not None else None  # None will use COHERE_API_KEY env var
        self.client = cohere.Client(api_key=api_key)

    @property
    def identifier(self) -> str:
        """Return strategy identifier."""
        return f"cohere-token-{self.chunk_size}"

    @property
    def max_output_tokens(self) -> int | None:
        """Return max output token limit."""
        return int(self.max_tokens)

    @property
    def supported_modalities(self) -> frozenset[ModalityType]:
        """Return supported modalities (TEXT only)."""
        return frozenset([ModalityType.TEXT])

    def supports_modality(self, modality: ModalityType) -> bool:
        """Check if strategy supports the modality."""
        return modality in self.supported_modalities

    def chunk(self, content: str | bytes) -> list[str | bytes]:
        """Split text into token-counted chunks with overlap using Cohere BPE tokenizer.

        Args:
            content: Text content to chunk

        Returns:
            List of text chunks

        Raises:
            TypeError: If content is not a string
            ValueError: If content is empty

        """
        if not isinstance(content, str):
            msg = f"Content must be str for TEXT modality, got {type(content)}"
            raise TypeError(msg)

        if not content or not content.strip():
            msg = "Content cannot be empty"
            raise ValueError(msg)

        text = content.strip()

        # Tokenize using Cohere SDK (BPE tokenization)
        tokenized = self.client.tokenize(text=text, model="embed-english-v3.0")
        tokens = tokenized.tokens  # List of token IDs

        # If text fits in one chunk, return it
        if len(tokens) <= self.chunk_size:
            return [text]

        # Split tokens into overlapping chunks
        chunks = []
        start = 0

        while start < len(tokens):
            # Get chunk tokens
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]

            # Ensure we don't exceed max_tokens
            if len(chunk_tokens) > self.max_tokens:
                chunk_tokens = chunk_tokens[: self.max_tokens]

            # Detokenize back to text
            detokenized = self.client.detokenize(tokens=chunk_tokens, model="embed-english-v3.0")
            chunk_text = detokenized.text
            chunks.append(str(chunk_text))

            # Move forward by (chunk_size - overlap)
            # Ensure we make progress even with large overlap
            step = max(1, self.chunk_size - self.chunk_overlap)
            start += step

        return chunks  # type: ignore[return-value]
