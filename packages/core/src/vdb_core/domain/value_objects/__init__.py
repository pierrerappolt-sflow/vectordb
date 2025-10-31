"""Value objects - immutable objects defined by their attributes.

Organized by domain concept:
- common/ - Base interfaces and shared VOs
- library/ - Library aggregate VOs
- document/ - Document VOs
- chunk/ - Chunk VOs
- embedding/ - Embedding and vector VOs
- strategy/ - Chunking/embedding strategy VOs
- config/ - Configuration VOs
- job/ - Job-related VOs
- query/ - Query VOs
"""

from .chunk import Chunk, ChunkId, ChunkStatus
from .common import ContentHash
from .config import ConfigStatus, VectorizationConfigId
from .embedding import EmbedInputType

# Document value objects
from .document import (
    MAX_FRAGMENT_SIZE_BYTES,
    DocumentFragmentId,
    DocumentId,
    DocumentName,
    DocumentStatus,
    ExtractedContent,
    ExtractedContentId,
    ExtractedContentStatus,
)

# Embedding value objects
from .embedding import Embedding, EmbeddingId, VectorIndexingStrategy, VectorSimilarityMetric

# Library value objects
from .library import LibraryId, LibraryName, LibraryStatus

# Strategy value objects
from .strategy import (
    ChunkingBehavior,
    ChunkingStrategyId,
    ChunkingStrategyStatus,
    EmbeddingStrategyId,
    EmbeddingStrategyStatus,
    ModalityType,
    ChunkingModelKey,
    EmbedModelKey,
)

__all__ = [
    # Document
    "MAX_FRAGMENT_SIZE_BYTES",
    # Chunk
    "Chunk",
    "ChunkId",
    "ChunkStatus",
    # Strategy
    "ChunkingBehavior",
    "ChunkingStrategyId",
    "ChunkingStrategyStatus",
    # Common
    "ContentHash",
    "DocumentFragmentId",
    "DocumentId",
    "DocumentName",
    "DocumentStatus",
    # Embedding
    "Embedding",
    "EmbeddingId",
    "VectorIndexingStrategy",
    "VectorSimilarityMetric",
    "EmbedInputType",
    # Config
    "EmbeddingStrategyId",
    "EmbeddingStrategyStatus",
    "ExtractedContent",
    "ExtractedContentId",
    "ExtractedContentStatus",
    # Library
    "LibraryId",
    "LibraryName",
    "LibraryStatus",
    "ModalityType",
    "VectorizationConfigId",
    "ConfigStatus",
    "ChunkingModelKey",
    "EmbedModelKey",
]
