"""PostgreSQL repository implementations for strategy entities.

This module contains repositories for:
- ChunkingStrategy
- EmbeddingStrategy
- VectorizationConfig (aggregate root)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from sqlalchemy import text

from vdb_core.domain.base import AbstractRepository
from vdb_core.domain.entities import ChunkingStrategy, EmbeddingStrategy, VectorizationConfig
from vdb_core.domain.exceptions import VectorizationConfigNotFoundError
from vdb_core.domain.value_objects import (
    ChunkingBehavior,
    ChunkingStrategyId,
    EmbeddingStrategyId,
    ModalityType,
    VectorIndexingStrategy,
    VectorizationConfigId,
    VectorSimilarityMetric,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PostgresChunkingStrategyRepository:
    """PostgreSQL repository for ChunkingStrategy entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self.session = session

    async def add(self, strategy: ChunkingStrategy) -> None:
        """Persist chunking strategy to database (idempotent)."""
        # Check if already exists
        result = await self.session.execute(
            text("SELECT id FROM chunking_strategies WHERE id = :id"),
            {"id": str(strategy.id)},
        )
        if result.scalar():
            # Already exists, skip
            return

        await self.session.execute(
            text("""
            INSERT INTO chunking_strategies (
                id, name, model_key, status, modality, behavior,
                chunk_size_tokens, chunk_overlap_tokens, min_chunk_size_tokens, max_chunk_size_tokens,
                max_content_size_bytes, max_width_pixels, max_height_pixels,
                frame_sample_rate_fps, max_frames, max_video_duration_seconds,
                segment_duration_seconds, segment_overlap_seconds, max_audio_duration_seconds,
                config, created_at, updated_at
            ) VALUES (
                :id, :name, :model_key, :status, :modality, :behavior,
                :chunk_size_tokens, :chunk_overlap_tokens, :min_chunk_size_tokens, :max_chunk_size_tokens,
                :max_content_size_bytes, :max_width_pixels, :max_height_pixels,
                :frame_sample_rate_fps, :max_frames, :max_video_duration_seconds,
                :segment_duration_seconds, :segment_overlap_seconds, :max_audio_duration_seconds,
                :config, :created_at, :updated_at
            )
            """),
            {
                "id": str(strategy.id),
                "name": strategy.name,
                "model_key": strategy.model_key,
                "status": strategy.status.value,
                "modality": strategy.modality.value.upper(),
                "behavior": strategy.behavior.value,
                "chunk_size_tokens": strategy.chunk_size_tokens,
                "chunk_overlap_tokens": strategy.chunk_overlap_tokens,
                "min_chunk_size_tokens": strategy.min_chunk_size_tokens,
                "max_chunk_size_tokens": strategy.max_chunk_size_tokens,
                "max_content_size_bytes": strategy.max_content_size_bytes,
                "max_width_pixels": strategy.max_width_pixels,
                "max_height_pixels": strategy.max_height_pixels,
                "frame_sample_rate_fps": strategy.frame_sample_rate_fps,
                "max_frames": strategy.max_frames,
                "max_video_duration_seconds": strategy.max_video_duration_seconds,
                "segment_duration_seconds": strategy.segment_duration_seconds,
                "segment_overlap_seconds": strategy.segment_overlap_seconds,
                "max_audio_duration_seconds": strategy.max_audio_duration_seconds,
                "config": json.dumps(strategy.config) if strategy.config else "{}",
                "created_at": strategy.created_at,
                "updated_at": strategy.updated_at,
            },
        )

    async def get(self, strategy_id: ChunkingStrategyId) -> ChunkingStrategy:
        """Retrieve chunking strategy by ID."""
        from vdb_core.domain.exceptions import ChunkingStrategyNotFoundError

        result = await self.session.execute(
            text("""
                SELECT id, name, model_key, status, modality, behavior,
                       chunk_size_tokens, chunk_overlap_tokens, min_chunk_size_tokens, max_chunk_size_tokens,
                       max_content_size_bytes, max_width_pixels, max_height_pixels,
                       frame_sample_rate_fps, max_frames, max_video_duration_seconds,
                       segment_duration_seconds, segment_overlap_seconds, max_audio_duration_seconds,
                       config, created_at, updated_at
                FROM chunking_strategies WHERE id = :id
            """),
            {"id": str(strategy_id)},
        )
        row = result.mappings().one_or_none()

        if not row:
            raise ChunkingStrategyNotFoundError(str(strategy_id))

        # Reconstitute domain entity
        from vdb_core.domain.value_objects import ChunkingStrategyStatus

        strategy = object.__new__(ChunkingStrategy)
        object.__setattr__(strategy, "id", ChunkingStrategyId(row["id"]))
        object.__setattr__(strategy, "name", row["name"])
        object.__setattr__(strategy, "model_key", row["model_key"])
        object.__setattr__(strategy, "status", ChunkingStrategyStatus(row["status"]))
        object.__setattr__(strategy, "modality", ModalityType(row["modality"]))
        object.__setattr__(strategy, "behavior", ChunkingBehavior(row["behavior"]))
        object.__setattr__(strategy, "chunk_size_tokens", row["chunk_size_tokens"])
        object.__setattr__(strategy, "chunk_overlap_tokens", row["chunk_overlap_tokens"])
        object.__setattr__(strategy, "min_chunk_size_tokens", row["min_chunk_size_tokens"])
        object.__setattr__(strategy, "max_chunk_size_tokens", row["max_chunk_size_tokens"])
        object.__setattr__(strategy, "max_content_size_bytes", row["max_content_size_bytes"])
        object.__setattr__(strategy, "max_width_pixels", row["max_width_pixels"])
        object.__setattr__(strategy, "max_height_pixels", row["max_height_pixels"])
        object.__setattr__(strategy, "frame_sample_rate_fps", row["frame_sample_rate_fps"])
        object.__setattr__(strategy, "max_frames", row["max_frames"])
        object.__setattr__(strategy, "max_video_duration_seconds", row["max_video_duration_seconds"])
        object.__setattr__(strategy, "segment_duration_seconds", row["segment_duration_seconds"])
        object.__setattr__(strategy, "segment_overlap_seconds", row["segment_overlap_seconds"])
        object.__setattr__(strategy, "max_audio_duration_seconds", row["max_audio_duration_seconds"])
        object.__setattr__(strategy, "config", row["config"] or {})
        object.__setattr__(strategy, "created_at", row["created_at"])
        object.__setattr__(strategy, "updated_at", row["updated_at"])
        object.__setattr__(strategy, "events", [])
        object.__setattr__(strategy, "_allow_setattr", False)

        return strategy


class PostgresEmbeddingStrategyRepository:
    """PostgreSQL repository for EmbeddingStrategy entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self.session = session

    async def add(self, strategy: EmbeddingStrategy) -> None:
        """Persist embedding strategy to database (idempotent)."""
        # Check if already exists
        result = await self.session.execute(
            text("SELECT id FROM embedding_strategies WHERE id = :id"),
            {"id": str(strategy.id)},
        )
        if result.scalar():
            # Already exists, skip
            return

        # Determine provider: prefer explicit config value, otherwise infer from model_key (current defaults are Cohere)
        provider_value = None
        try:
                provider_value = strategy.config.get("provider")
        except Exception:
            provider_value = None
        if not provider_value:
            provider_value = "cohere"

        await self.session.execute(
            text("""
            INSERT INTO embedding_strategies (
                id, name, model_key, status, modality,
                dimensions, provider, model_name,
                max_tokens, max_image_size_bytes, max_width_pixels, max_height_pixels,
                config, created_at, updated_at
            ) VALUES (
                :id, :name, :model_key, :status, :modality,
                :dimensions, :provider, :model_name,
                :max_tokens, :max_image_size_bytes, :max_width_pixels, :max_height_pixels,
                :config, :created_at, :updated_at
            )
            """),
            {
                "id": str(strategy.id),
                "name": strategy.name,
                "model_key": strategy.model_key,
                "status": strategy.status.value,
                "modality": strategy.modality.value,
                "dimensions": strategy.dimensions,
                "provider": provider_value,
                "model_name": strategy.model_name,
                "max_tokens": strategy.max_tokens,
                "max_image_size_bytes": strategy.max_image_size_bytes,
                "max_width_pixels": None,
                "max_height_pixels": None,
                "config": json.dumps(strategy.config) if strategy.config else "{}",
                "created_at": strategy.created_at,
                "updated_at": strategy.updated_at,
            },
        )

    async def get(self, strategy_id: EmbeddingStrategyId) -> EmbeddingStrategy:
        """Retrieve embedding strategy by ID."""
        from vdb_core.domain.exceptions import EmbeddingStrategyNotFoundError

        result = await self.session.execute(
            text("""
                SELECT id, name, model_key, status, modality,
                       dimensions, provider, model_name,
                       max_tokens, max_image_size_bytes, max_width_pixels, max_height_pixels,
                       config, created_at, updated_at
                FROM embedding_strategies WHERE id = :id
            """),
            {"id": str(strategy_id)},
        )
        row = result.mappings().one_or_none()

        if not row:
            raise EmbeddingStrategyNotFoundError(str(strategy_id))

        # Reconstitute domain entity (simplified for brevity)
        from vdb_core.domain.value_objects import (
            EmbeddingStrategyStatus,
        )

        strategy = object.__new__(EmbeddingStrategy)
        object.__setattr__(strategy, "id", EmbeddingStrategyId(row["id"]))
        object.__setattr__(strategy, "name", row["name"])
        object.__setattr__(strategy, "model_key", row["model_key"])
        object.__setattr__(strategy, "status", EmbeddingStrategyStatus(row["status"]))
        object.__setattr__(strategy, "modality", ModalityType(row["modality"]))
        object.__setattr__(strategy, "dimensions", row["dimensions"])
        object.__setattr__(strategy, "model_name", row["model_name"])
        object.__setattr__(strategy, "max_tokens", row["max_tokens"])
        object.__setattr__(strategy, "max_image_size_bytes", row["max_image_size_bytes"])
        object.__setattr__(strategy, "config", row["config"] or {})
        object.__setattr__(strategy, "created_at", row["created_at"])
        object.__setattr__(strategy, "updated_at", row["updated_at"])
        object.__setattr__(strategy, "events", [])
        object.__setattr__(strategy, "_allow_setattr", False)

        return strategy


class PostgresVectorizationConfigRepository(AbstractRepository[VectorizationConfig, VectorizationConfigId]):
    """PostgreSQL repository for VectorizationConfig aggregate root.

    Responsibilities:
    - Persist VectorizationConfig entities
    - Automatically persist associated ChunkingStrategy and EmbeddingStrategy entities
    - Handle version chains and config evolution
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session for database operations

        """
        super().__init__()  # Initialize seen/added tracking
        self.session = session
        # Create strategy repositories for cascading persistence
        self.chunking_repo = PostgresChunkingStrategyRepository(session)
        self.embedding_repo = PostgresEmbeddingStrategyRepository(session)

    async def _add(self, config: VectorizationConfig) -> None:
        """Persist vectorization config and its associated strategies.

        This method follows the aggregate pattern:
        1. Persist all chunking strategies (if not already in DB)
        2. Persist all embedding strategies (if not already in DB)
        3. Persist the config itself with strategy ID references

        Args:
            config: VectorizationConfig entity to persist

        """
        # Step 1: Persist all chunking strategies referenced by this config
        for chunking_strategy in config.chunking_strategies:
            await self.chunking_repo.add(chunking_strategy)

        # Step 2: Persist all embedding strategies referenced by this config
        await self.embedding_repo.add(config.embedding_strategy)

        # Step 3: Now persist the config itself with strategy ID arrays
        chunking_ids = [str(strategy.id) for strategy in config.chunking_strategies]
        embedding_ids = [str(config.embedding_strategy.id)]

        await self.session.execute(
            text("""
            INSERT INTO vectorization_configs (
                id, version, status, previous_version_id, description,
                chunking_strategy_ids, embedding_strategy_ids,
                vector_indexing_strategy, vector_similarity_metric,
                created_at, updated_at
            ) VALUES (
                :id, :version, :status, :previous_version_id, :description,
                :chunking_strategy_ids, :embedding_strategy_ids,
                :vector_indexing_strategy, :vector_similarity_metric,
                :created_at, :updated_at
            )
            """),
            {
                "id": str(config.id),
                "version": config.version,
                "status": config.status,
                "previous_version_id": str(config.previous_version_id) if config.previous_version_id else None,
                "description": config.description,
                "chunking_strategy_ids": chunking_ids,
                "embedding_strategy_ids": embedding_ids,
                "vector_indexing_strategy": config.vector_indexing_strategy,
                "vector_similarity_metric": config.vector_similarity_metric,
                "created_at": config.created_at,
                "updated_at": config.updated_at,
            },
        )

    async def _get(self, config_id: VectorizationConfigId) -> VectorizationConfig | None:
        """Retrieve vectorization config by ID with full strategy entities.

        Args:
            config_id: ID of the config to retrieve

        Returns:
            VectorizationConfig entity with loaded strategy entities, or None if not found

        """
        result = await self.session.execute(
            text("""
                SELECT id, version, status, previous_version_id, description,
                       chunking_strategy_ids, embedding_strategy_ids,
                       vector_indexing_strategy, vector_similarity_metric,
                       created_at, updated_at
                FROM vectorization_configs
                WHERE id = :id
            """),
            {"id": str(config_id)},
        )
        row = result.mappings().one_or_none()

        if not row:
            return None

        # Load full strategy entities from IDs
        chunking_strategies = []
        for strategy_id in row["chunking_strategy_ids"]:
            strategy = await self.chunking_repo.get(ChunkingStrategyId(strategy_id))
            chunking_strategies.append(strategy)

        # Load single embedding strategy (first from array)
        embedding_strategy = None
        for emb_strategy_id in row["embedding_strategy_ids"]:
            embedding_strategy = await self.embedding_repo.get(EmbeddingStrategyId(emb_strategy_id))
            break

        # Reconstitute config entity

        config = object.__new__(VectorizationConfig)
        object.__setattr__(config, "id", VectorizationConfigId(row["id"]))
        object.__setattr__(config, "version", row["version"])
        object.__setattr__(config, "status", row["status"])
        object.__setattr__(
            config,
            "previous_version_id",
            VectorizationConfigId(row["previous_version_id"]) if row["previous_version_id"] else None,
        )
        object.__setattr__(config, "description", row["description"])
        object.__setattr__(config, "chunking_strategies", chunking_strategies)
        if embedding_strategy is None:
            from vdb_core.domain.exceptions import EmbeddingStrategyNotFoundError
            raise EmbeddingStrategyNotFoundError("No embedding strategy found for config")
        object.__setattr__(config, "embedding_strategy", embedding_strategy)
        object.__setattr__(
            config,
            "vector_indexing_strategy",
            VectorIndexingStrategy(row["vector_indexing_strategy"]),
        )
        object.__setattr__(
            config,
            "vector_similarity_metric",
            VectorSimilarityMetric(row["vector_similarity_metric"]),
        )
        object.__setattr__(config, "created_at", row["created_at"])
        object.__setattr__(config, "updated_at", row["updated_at"])
        object.__setattr__(config, "events", [])
        object.__setattr__(config, "_allow_setattr", False)

        return config

    async def _update(self, config: VectorizationConfig) -> None:
        """Update existing vectorization config.

        Note: Configs are immutable by design (version chains).
        Updates should create new versions via create_new_version().
        """
        await self.session.execute(
            text("""
                UPDATE vectorization_configs
                SET status = :status,
                    description = :description,
                    updated_at = :updated_at
                WHERE id = :id
            """),
            {
                "id": str(config.id),
                "status": config.status,
                "description": config.description,
                "updated_at": config.updated_at,
            },
        )

    async def list(self) -> list[VectorizationConfig]:
        """List all vectorization configs.

        Returns:
            List of all VectorizationConfig entities

        """
        result = await self.session.execute(
            text("""
                SELECT id, version, status, previous_version_id, description,
                       chunking_strategy_ids, embedding_strategy_ids,
                       vector_indexing_strategy, vector_similarity_metric,
                       created_at, updated_at
                FROM vectorization_configs
                ORDER BY created_at DESC
            """)
        )
        rows = result.mappings().all()

        configs = []
        for row in rows:
            # Load full strategy entities (simplified - could optimize with bulk load)
            chunking_strategies = []
            for strategy_id in row["chunking_strategy_ids"]:
                strategy = await self.chunking_repo.get(ChunkingStrategyId(strategy_id))
                chunking_strategies.append(strategy)

            # Load single embedding strategy from array
            embedding_strategy = None
            for emb_strat_id in row["embedding_strategy_ids"]:
                emb_strat = await self.embedding_repo.get(EmbeddingStrategyId(emb_strat_id))
                embedding_strategy = emb_strat
                break

            # Reconstitute config

            config = object.__new__(VectorizationConfig)
            object.__setattr__(config, "id", VectorizationConfigId(row["id"]))
            object.__setattr__(config, "version", row["version"])
            object.__setattr__(config, "status", row["status"])
            object.__setattr__(
                config,
                "previous_version_id",
                VectorizationConfigId(row["previous_version_id"]) if row["previous_version_id"] else None,
            )
            object.__setattr__(config, "description", row["description"])
            object.__setattr__(config, "chunking_strategies", chunking_strategies)
            if embedding_strategy is None:
                from vdb_core.domain.exceptions import EmbeddingStrategyNotFoundError
                raise EmbeddingStrategyNotFoundError("No embedding strategy found for config")
            object.__setattr__(config, "embedding_strategy", embedding_strategy)
            object.__setattr__(
                config,
                "vector_indexing_strategy",
                VectorIndexingStrategy(row["vector_indexing_strategy"]),
            )
            object.__setattr__(
                config,
                "vector_similarity_metric",
                VectorSimilarityMetric(row["vector_similarity_metric"]),
            )
            object.__setattr__(config, "created_at", row["created_at"])
            object.__setattr__(config, "updated_at", row["updated_at"])
            object.__setattr__(config, "events", [])
            object.__setattr__(config, "_allow_setattr", False)

            configs.append(config)

        return configs

    async def _delete(self, config_id: VectorizationConfigId) -> None:
        """Hard delete a vectorization config.

        Note: This does not delete associated strategies (they may be used by other configs).

        Args:
            config_id: ID of the config to delete

        Raises:
            VectorizationConfigNotFoundError: If config not found

        """
        result = await self.session.execute(
            text("DELETE FROM vectorization_configs WHERE id = :id RETURNING id"),
            {"id": str(config_id)},
        )
        if not result.scalar():
            raise VectorizationConfigNotFoundError(str(config_id))

    async def _soft_delete(self, config: VectorizationConfig) -> None:
        """Soft delete a vectorization config by marking it as DEPRECATED.

        Args:
            config: The config entity to soft delete

        """
        await self.session.execute(
            text("""
                UPDATE vectorization_configs
                SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {"id": str(config.id), "status": "deprecated"},
        )

    def stream(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> AsyncIterator[VectorizationConfig]:
        """Stream vectorization configs for memory-efficient iteration.

        Args:
            skip: Number of configs to skip
            limit: Maximum number of configs to yield

        Yields:
            VectorizationConfig entities

        """
        async def _stream_generator() -> AsyncIterator[VectorizationConfig]:
            # Build query with pagination
            query = text("""
                SELECT id, version, status, previous_version_id, description,
                       chunking_strategy_ids, embedding_strategy_ids,
                       vector_indexing_strategy, vector_similarity_metric,
                       created_at, updated_at
                FROM vectorization_configs
                ORDER BY created_at DESC
                OFFSET :skip
                LIMIT :limit
            """)

            params = {"skip": skip, "limit": limit if limit else 10000}
            result = await self.session.execute(query, params)

            for row in result.mappings():
                # Load full strategy entities
                chunking_strategies = []
                for strategy_id in row["chunking_strategy_ids"]:
                    strategy = await self.chunking_repo.get(ChunkingStrategyId(strategy_id))
                    chunking_strategies.append(strategy)

                # Load single embedding strategy from array
                embedding_strategy = None
                for emb_strat_id in row["embedding_strategy_ids"]:
                    emb_strat = await self.embedding_repo.get(EmbeddingStrategyId(emb_strat_id))
                    embedding_strategy = emb_strat
                    break

                # Reconstitute config

                config = object.__new__(VectorizationConfig)
                object.__setattr__(config, "id", VectorizationConfigId(row["id"]))
                object.__setattr__(config, "version", row["version"])
                object.__setattr__(config, "status", "active")
                object.__setattr__(
                    config,
                    "previous_version_id",
                    VectorizationConfigId(row["previous_version_id"]) if row["previous_version_id"] else None,
                )
                object.__setattr__(config, "description", row["description"])
                object.__setattr__(config, "chunking_strategies", chunking_strategies)
                if embedding_strategy is None:
                    from vdb_core.domain.exceptions import EmbeddingStrategyNotFoundError
                    raise EmbeddingStrategyNotFoundError("No embedding strategy found for config")
                object.__setattr__(config, "embedding_strategy", embedding_strategy)
                object.__setattr__(
                    config,
                    "vector_indexing_strategy",
                    VectorIndexingStrategy(row["vector_indexing_strategy"]),
                )
                object.__setattr__(
                    config,
                    "vector_similarity_metric",
                    VectorSimilarityMetric(row["vector_similarity_metric"]),
                )
                object.__setattr__(config, "created_at", row["created_at"])
                object.__setattr__(config, "updated_at", row["updated_at"])
                object.__setattr__(config, "events", [])
                object.__setattr__(config, "_allow_setattr", False)

                yield config

        return _stream_generator()
