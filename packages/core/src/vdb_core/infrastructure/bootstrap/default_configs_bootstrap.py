"""Bootstrap service to create default Cohere vectorization configs on startup."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, cast

from vdb_core.domain.entities import ChunkingStrategy, EmbeddingStrategy, VectorizationConfig
from vdb_core.domain.value_objects import (
    ChunkingBehavior,
    ChunkingStrategyId,
    EmbeddingStrategyId,
    EmbeddingStrategyStatus,
    ModalityType,
    VectorIndexingStrategy,
    VectorSimilarityMetric,
)
from vdb_core.domain.value_objects.strategy.model_key import (
    ChunkingModelKey,
    EmbedModelKey,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vdb_core.application.i_unit_of_work import IUnitOfWork

logger = logging.getLogger(__name__)


# Model configurations for default Cohere vectorization configs
# Used by bootstrap service and integration tests (single source of truth)
DEFAULT_COHERE_MODEL_CONFIGS = [
    {
        "name": "Cohere English v3",
        "dims": "1024d",
        "chunking": ChunkingStrategy(
            name="Cohere Token Chunking (256 tokens)",
            model_key=ChunkingModelKey.COHERE_TOKEN_256.value,
            modality=ModalityType.TEXT,
            behavior=ChunkingBehavior.SPLIT,
            chunk_size_tokens=256,
            chunk_overlap_tokens=25,
            min_chunk_size_tokens=50,
            max_chunk_size_tokens=512,
            config={"max_tokens": 512},
        ),
        "embedding": EmbeddingStrategy(
            name="Cohere English v3 (1024d)",
            model_key=EmbedModelKey.EMBED_ENGLISH_V3.value,
            modality=ModalityType.TEXT,
            dimensions=1024,
            status=EmbeddingStrategyStatus.ACTIVE,
            model_name="embed-english-v3.0",
            max_tokens=512,
        ),
    },
    {
        "name": "Cohere Multilingual v3",
        "dims": "1024d",
        "chunking": ChunkingStrategy(
            name="Cohere Token Chunking (256 tokens)",
            model_key=ChunkingModelKey.COHERE_TOKEN_256.value,
            modality=ModalityType.TEXT,
            behavior=ChunkingBehavior.SPLIT,
            chunk_size_tokens=256,
            chunk_overlap_tokens=25,
            min_chunk_size_tokens=50,
            max_chunk_size_tokens=512,
            config={"max_tokens": 512},
        ),
        "embedding": EmbeddingStrategy(
            name="Cohere Multilingual v3 (1024d)",
            model_key=EmbedModelKey.EMBED_MULTILINGUAL_V3.value,
            modality=ModalityType.TEXT,
            dimensions=1024,
            status=EmbeddingStrategyStatus.ACTIVE,
            model_name="embed-multilingual-v3.0",
            max_tokens=512,
        ),
    },
    {
        "name": "Cohere English Light v3",
        "dims": "384d",
        "chunking": ChunkingStrategy(
            name="Cohere Token Chunking (256 tokens)",
            model_key=ChunkingModelKey.COHERE_TOKEN_256.value,
            modality=ModalityType.TEXT,
            behavior=ChunkingBehavior.SPLIT,
            chunk_size_tokens=256,
            chunk_overlap_tokens=25,
            min_chunk_size_tokens=50,
            max_chunk_size_tokens=512,
            config={"max_tokens": 512},
        ),
        "embedding": EmbeddingStrategy(
            name="Cohere English Light v3 (384d)",
            model_key=EmbedModelKey.EMBED_ENGLISH_LIGHT_V3.value,
            modality=ModalityType.TEXT,
            dimensions=384,
            status=EmbeddingStrategyStatus.ACTIVE,
            model_name="embed-english-light-v3.0",
            max_tokens=512,
        ),
    },
    {
        "name": "Cohere Multilingual Light v3",
        "dims": "384d",
        "chunking": ChunkingStrategy(
            name="Cohere Token Chunking (256 tokens)",
            model_key=ChunkingModelKey.COHERE_TOKEN_256.value,
            modality=ModalityType.TEXT,
            behavior=ChunkingBehavior.SPLIT,
            chunk_size_tokens=256,
            chunk_overlap_tokens=25,
            min_chunk_size_tokens=50,
            max_chunk_size_tokens=512,
            config={"max_tokens": 512},
        ),
        "embedding": EmbeddingStrategy(
            name="Cohere Multilingual Light v3 (384d)",
            model_key=EmbedModelKey.EMBED_MULTILINGUAL_LIGHT_V3.value,
            modality=ModalityType.TEXT,
            dimensions=384,
            status=EmbeddingStrategyStatus.ACTIVE,
            model_name="embed-multilingual-light-v3.0",
            max_tokens=512,
        ),
    },
]


class DefaultConfigsBootstrap:
    """Bootstrap service to create default Cohere vectorization configs.

    Creates on first startup (idempotent - checks if already exists):
    - 1 chunking strategy:
      - CohereTokenChunker (256 tokens) for v3 text models
    - 4 embedding strategies (v3 text-only)
    - 4 vectorization configs (one per model, all with COSINE similarity)

    All configs use:
    - FLAT indexing (simplest)
    - COSINE similarity metric (hardcoded)
    """

    BOOTSTRAP_MARKER_KEY = "default_cohere_configs_v1"

    def __init__(self, uow_factory: Callable[[], IUnitOfWork]) -> None:
        """Initialize bootstrap service.

        Args:
            uow_factory: Factory to create Unit of Work instances

        """
        self.uow_factory = uow_factory

    async def bootstrap_default_configs(self) -> None:
        """Create default configs if they don't exist (idempotent).

        Creates vectorization configs with embedded strategies:
        - 4 embedding strategies (v3 text-only)
        - 1 chunking strategy (256 token)
        - 4 vectorization configs (one per model, all with COSINE similarity)

        Strategies are created within VectorizationConfig aggregate (not separately).
        All configs use type-safe ModelKey enums to prevent typos.
        """
        logger.info("Bootstrapping default Cohere vectorization configs...")

        async with self.uow_factory() as uow:
            # Check if already bootstrapped
            try:
                # Check if any configs exist (repository may not implement list)
                list_method = getattr(uow.vectorization_configs, "list", None)
                if callable(list_method):
                    existing = await list_method()
                    if existing:
                        logger.info("Default configs already exist, skipping bootstrap")
                        return
            except Exception:
                # Repository doesn't support list or error occurred, proceed with bootstrap
                pass

            # Create vectorization configs with embedded strategies
            await self._create_vectorization_configs(uow)

            await uow.commit()
            logger.info("✅ Default Cohere configs bootstrapped successfully")

    async def _create_vectorization_configs(self, uow: IUnitOfWork) -> None:
        """Create vectorization configs with embedded strategies.

        Creates 4 configs (one per model, all with COSINE similarity):

        Models:
        - Cohere English v3 (1024d, text-only)
        - Cohere Multilingual v3 (1024d, text-only)
        - Cohere English Light v3 (384d, text-only)
        - Cohere Multilingual Light v3 (384d, text-only)

        Similarity Metric:
        - COSINE (angle-based, standard for text) - hardcoded

        Chunking:
        - All v3 configs: CohereTokenChunker (256 tokens, 512 max) for TEXT

        All use:
        - FLAT indexing (simplest)
        - Type-safe ModelKey enums (prevents typos)
        """
        logger.info("Creating vectorization configs with embedded strategies...")

        config_count = 0

        # Use module-level default configs (single source of truth)
        models = DEFAULT_COHERE_MODEL_CONFIGS

        # Step 1: Set deterministic IDs on strategies
        # Use stable UUID generation based on model_key to ensure idempotency
        unique_chunking_strategies = {}  # model_key -> strategy
        unique_embedding_strategies = {}  # model_key -> strategy

        for model_config in models:
            chunking = model_config["chunking"]  # ChunkingStrategy or list[ChunkingStrategy]

            # Handle both single chunker (v3) and multiple chunkers (v4 multimodal)
            chunkers: list[ChunkingStrategy] = [chunking] if not isinstance(chunking, list) else chunking  # type: ignore[list-item]

            for chunker in chunkers:
                # Use model_key as stable identifier for deterministic UUID
                if chunker.model_key not in unique_chunking_strategies:
                    # Create deterministic UUID from model_key (namespace UUID5)
                    namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")  # null namespace
                    deterministic_id = uuid.uuid5(namespace, f"chunking:{chunker.model_key}")
                    object.__setattr__(chunker, "id", ChunkingStrategyId(deterministic_id))
                    unique_chunking_strategies[chunker.model_key] = chunker

        # Track unique embedding strategies by model_key and assign deterministic IDs
        for model_config in models:
            embedding_strategy = cast("EmbeddingStrategy", model_config["embedding"])
            if embedding_strategy.model_key not in unique_embedding_strategies:
                # Create deterministic UUID from model_key (namespace UUID5)
                namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")  # null namespace
                deterministic_id = uuid.uuid5(namespace, f"embedding:{embedding_strategy.model_key}")
                object.__setattr__(embedding_strategy, "id", EmbeddingStrategyId(deterministic_id))
                unique_embedding_strategies[embedding_strategy.model_key] = embedding_strategy

        logger.info("  - Generated deterministic IDs for %d chunking + %d embedding strategies",
                   len(unique_chunking_strategies), len(unique_embedding_strategies))

        # Step 2: Create configs (repository will auto-persist strategies)
        logger.info("  - Creating vectorization configs (strategies will be auto-persisted)...")
        for model_config in models:
            chunking_obj = cast("ChunkingStrategy", model_config["chunking"])
            embedding_obj = cast("EmbeddingStrategy", model_config["embedding"])

            # v3 models use single chunker
            chunking_strategies: list[ChunkingStrategy] = [chunking_obj]

            # Create config with COSINE similarity and FLAT indexing
            config = VectorizationConfig(
                version=1,
                description=f"{model_config['name']} ({model_config['dims']}) with Cosine similarity - FLAT indexing",
                chunking_strategies=chunking_strategies,
                embedding_strategy=embedding_obj,
                vector_indexing_strategy=VectorIndexingStrategy.FLAT,
                vector_similarity_metric=VectorSimilarityMetric.COSINE,
            )
            await uow.vectorization_configs.add(config)
            config_count += 1

        logger.info("  ✅ Created %d vectorization configs", config_count)
        logger.info("     (4 v3 text models with COSINE similarity = %d configs)", config_count)
        logger.info("     Repository auto-persisted: %d chunking + %d embedding strategies",
                   len(unique_chunking_strategies), len(unique_embedding_strategies))
