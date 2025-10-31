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

# Common/shared value objects
# Chunk value objects
from .chunk import Chunk, ChunkId, ChunkStatus, ChunkStatusEnum, default_chunk_status
from .common import ContentHash, Status

# Config value objects
from .config import EmbeddingProvider, VectorizationConfigId

# Document value objects
from .document import (
    MAX_FRAGMENT_SIZE_BYTES,
    DocumentFragmentId,
    DocumentId,
    DocumentName,
    DocumentStatus,
    DocumentStatusEnum,
    ExtractedContent,
    ExtractedContentId,
    ExtractedContentStatus,
    ExtractedContentStatusEnum,
    default_document_status,
    default_extracted_content_status,
)

# Embedding value objects
from .embedding import (
    Embedding,
    EmbeddingId,
    VectorIndexingStrategy,
    VectorIndexingStrategyEnum,
    VectorSimilarityMetric,
    VectorSimilarityMetricEnum,
)

# Job value objects
from .job import (
    IngestionJobId,
    IngestionJobStatus,
    IngestionJobStatusEnum,
    VectorizationJobId,
    VectorizationJobStatus,
    VectorizationJobStatusEnum,
    default_ingestion_job_status,
    default_vectorization_job_status,
)

# Library value objects
from .library import LibraryId, LibraryName, LibraryStatus, LibraryStatusEnum, default_library_status

# Query value objects
from .query import QueryId, QueryStatus, QueryStatusEnum, default_query_status

# Strategy value objects
from .strategy import (
    ChunkingBehavior,
    ChunkingStrategyId,
    ChunkingStrategyStatus,
    ChunkingStrategyStatusEnum,
    EmbeddingStrategyId,
    EmbeddingStrategyStatus,
    EmbeddingStrategyStatusEnum,
    ModalityType,
    ModalityTypeEnum,
    default_chunking_strategy_status,
    default_embedding_strategy_status,
)

__all__ = [
    # Document
    "MAX_FRAGMENT_SIZE_BYTES",
    # Chunk
    "Chunk",
    "ChunkId",
    "ChunkStatus",
    "ChunkStatusEnum",
    # Strategy
    "ChunkingBehavior",
    "ChunkingStrategyId",
    "ChunkingStrategyStatus",
    "ChunkingStrategyStatusEnum",
    # Common
    "ContentHash",
    "DocumentFragmentId",
    "DocumentId",
    "DocumentName",
    "DocumentStatus",
    "DocumentStatusEnum",
    # Embedding
    "Embedding",
    # Config
    "EmbeddingId",
    "EmbeddingProvider",
    "EmbeddingStrategyId",
    "EmbeddingStrategyStatus",
    "EmbeddingStrategyStatusEnum",
    "ExtractedContent",
    "ExtractedContentId",
    "ExtractedContentStatus",
    "ExtractedContentStatusEnum",
    # Job
    "IngestionJobId",
    "IngestionJobStatus",
    "IngestionJobStatusEnum",
    # Library
    "LibraryId",
    "LibraryName",
    "LibraryStatus",
    "LibraryStatusEnum",
    "ModalityType",
    "ModalityTypeEnum",
    # Query
    "QueryId",
    "QueryStatus",
    "QueryStatusEnum",
    "Status",
    "VectorIndexingStrategy",
    "VectorIndexingStrategyEnum",
    "VectorSimilarityMetric",
    "VectorSimilarityMetricEnum",
    "VectorizationConfigId",
    "VectorizationJobId",
    "VectorizationJobStatus",
    "VectorizationJobStatusEnum",
    "default_chunk_status",
    "default_chunking_strategy_status",
    "default_document_status",
    "default_embedding_strategy_status",
    "default_extracted_content_status",
    "default_ingestion_job_status",
    "default_library_status",
    "default_query_status",
    "default_vectorization_job_status",
]
