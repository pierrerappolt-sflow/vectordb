"""EmbedInputType value object - specifies the purpose of embedding generation."""

from enum import StrEnum, auto
from typing import final


@final
class EmbedInputType(StrEnum):
    """Enum for embedding input types.

    Used by embedding services to optimize embeddings for different use cases:
    - SEARCH: For query embeddings (used at search/query time) → "search"
    - DOCUMENT: For document/chunk embeddings (used during indexing) → "document"

    Some embedding models (like Cohere) use this to generate different
    representations optimized for retrieval vs indexing.

    The auto() function generates lowercase string values from the enum names.
    """

    SEARCH = auto()  # → "search" - For search queries
    DOCUMENT = auto()  # → "document" - For document chunks during indexing
