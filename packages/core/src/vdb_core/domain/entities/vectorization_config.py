"""VectorizationConfig entity - configuration for document-to-vector transformation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import uuid4

from vdb_core.domain.base import IEntity, DomainEvent
from vdb_core.domain.value_objects import (
    ModalityType,
    VectorIndexingStrategy,
    VectorizationConfigId,
    VectorSimilarityMetric,
)
if TYPE_CHECKING:
    from vdb_core.domain.entities import ChunkingStrategy, EmbeddingStrategy


@dataclass(slots=True, kw_only=True, eq=False)
class VectorizationConfig(IEntity):
    """Global vectorization configuration with immutable versioning.

    Defines the complete vectorization pipeline for document-to-vector transformation:
    1. Chunking: How to split documents (by modality)
    2. Embedding: How to generate vectors
    3. Indexing: How to store vectors (and compress them)
    4. Search: How to measure similarity

    Architecture (post-refactoring):
    - Configs are GLOBAL entities (not owned by libraries)
    - Configs are IMMUTABLE with versioning (any edit creates new version)
    - Libraries associate with configs via many-to-many relationship
    - Libraries can use multiple configs simultaneously

    Versioning:
    - Each config has a version number (starts at 1)
    - Editing creates new version with incremented number
    - previous_version_id links to parent version (version chain)

    Status Lifecycle:
    - DRAFT: Config created but not yet active
    - ACTIVE: Config available for use
    - ARCHIVED: Not in use, archived for historical reference

    Attributes:
        id: Unique identifier for this config
        version: Version number (increments with each edit, immutable)
        status: Lifecycle status
        previous_version_id: Link to previous version (for version chain)
        description: Human-readable description of this config/version
        chunking_strategies: List of chunking strategy entities
        embedding_strategies: List of embedding strategy entities
        vector_indexing_strategy: Data structure for storing vectors
        vector_similarity_metric: How to measure vector similarity

    Invariants:
        - At least one chunking strategy
        - Exactly ONE embedding strategy (not zero, not multiple)
        - No duplicate modalities in chunking strategies
        - If embedding strategy is single-modality, at least one chunker must match its modality
        - If embedding strategy is MULTIMODAL, no matching validation needed
        - version >= 1
        - If previous_version_id exists, version > 1

        Open Question:
        - Currently we allow any combination of strategies/metrics,
          we could enforce a more strict rule here.

    Strategy Resolution:
        The config holds actual strategy entity references. These are loaded by the repository
        when reconstituting the entity from persistence. Modality routing is done by checking
        the modality attribute of each strategy entity.

    Example 1 (text-only configuration):
            text_chunker = ChunkingStrategy(
                name="Cohere Token Chunking",
                model_key="cohere-token-256",
                modality=ModalityType.TEXT,
                behavior=ChunkingBehavior.SPLIT,
                chunk_size_tokens=256,
                chunk_overlap_tokens=25,
                max_chunk_size_tokens=512,
            )
            text_embedder = EmbeddingStrategy(
                name="Cohere English v3",
                model_key="cohere/embed-english-v3.0",
                modality=ModalityType.TEXT,
                dimensions=1024,
                max_tokens=512,
                status=EmbeddingStrategyStatus.ACTIVE,
                model_name="embed-english-v3.0",
            )
            config = VectorizationConfig(
                version=1,
                status=VectorizationConfigStatus.ACTIVE,
                description="Default text-only configuration",
                chunking_strategies=[text_chunker],
                embedding_strategies=[text_embedder],  # Exactly ONE
            )

    Example 2 (multimodal configuration):
            text_chunker = ChunkingStrategy(
                name="Cohere Token Chunking",
                model_key="cohere-token-256",
                modality=ModalityType.TEXT,
                behavior=ChunkingBehavior.SPLIT,
                chunk_size_tokens=256,
                chunk_overlap_tokens=25,
            )
            image_chunker = ChunkingStrategy(
                name="Passthrough Image",
                model_key="passthrough-image",
                modality=ModalityType(ModalityType.IMAGE),
                behavior=ChunkingBehavior.PASSTHROUGH,
            )
            multimodal_embedder = EmbeddingStrategy(
                name="Cohere Multimodal v4",
                model_key="cohere/embed-multimodal-v4.0",
                modality=ModalityType(ModalityType.MULTIMODAL),
                dimensions=1024,
                status=EmbeddingStrategyStatus.ACTIVE,
                model_name="embed-multimodal-v4.0",
            )
            config = VectorizationConfig(
                version=1,
                status=VectorizationConfigStatus.ACTIVE,
                description="Multimodal text+image configuration",
                chunking_strategies=[text_chunker, image_chunker],
                embedding_strategies=[multimodal_embedder],  # ONE MULTIMODAL embedder
            )
    """

    id: VectorizationConfigId = field(default_factory=lambda: VectorizationConfigId(uuid4()), init=False)
    version: int
    status: str = "active"
    previous_version_id: VectorizationConfigId | None = None
    description: str | None = None
    chunking_strategies: list[ChunkingStrategy]
    embedding_strategy: EmbeddingStrategy
    vector_indexing_strategy: VectorIndexingStrategy = VectorIndexingStrategy.FLAT
    vector_similarity_metric: VectorSimilarityMetric = VectorSimilarityMetric.COSINE

    def __post_init__(self) -> None:
        """Validate configuration invariants.

        Enforces invariants:
        1. version >= 1
        2. If previous_version_id exists, version > 1
        3. At least one chunking strategy
        4. Exactly ONE embedding strategy
        5. No duplicate modalities in chunking strategies
        6. If embedding is single-modality, at least one chunker must match

        Raises:
            ValueError: If any invariant is violated

        """

        # Invariant 1: version >= 1
        if self.version < 1:
            msg = f"VectorizationConfig version must be >= 1, got {self.version}"
            raise ValueError(msg)

        # Invariant 2: If previous_version_id exists, version > 1
        if self.previous_version_id is not None and self.version <= 1:
            msg = f"VectorizationConfig with previous_version_id must have version > 1, got {self.version}"
            raise ValueError(msg)

        # Invariant 3: At least one chunking strategy
        if not self.chunking_strategies:
            msg = "VectorizationConfig must have at least one chunking strategy"
            raise ValueError(msg)

        # Invariant 4: Exactly ONE embedding strategy
        if not self.embedding_strategy:
            msg = "VectorizationConfig must have exactly ONE embedding strategy"
            raise ValueError(msg)

        # Invariant 5: If embedding is single-modality, at least one chunker must match
        embedding_modality = self.embedding_strategy.modality
        if embedding_modality != ModalityType.MULTIMODAL:
            if self.chunking_strategies[0].modality != embedding_modality:
                msg = "VectorizationConfig has embedding strategy but no matching chunking strategy"
                raise ValueError(msg)

        # Call parent __post_init__ directly due to slots=True issue with super()
        IEntity.__post_init__(self)

    def collect_all_events(self) -> list[DomainEvent]:
        """Collect events from this aggregate.

        Unlike Library which has child entities, VectorizationConfig is a simpler
        aggregate that only has its own events. This method returns the entity's
        own events and clears them.

        Returns:
            All events from this entity

        """
        events = self.events.copy()
        self.events.clear()
        return events
