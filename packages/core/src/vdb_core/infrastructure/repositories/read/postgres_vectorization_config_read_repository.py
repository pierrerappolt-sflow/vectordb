"""PostgreSQL implementation of VectorizationConfig read repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import VectorizationConfigReadModel
from vdb_core.application.repositories import IVectorizationConfigReadRepository

if TYPE_CHECKING:
    import asyncpg


class PostgresVectorizationConfigReadRepository(IVectorizationConfigReadRepository):
    """PostgreSQL implementation of VectorizationConfig read repository.

    Queries vectorization_configs directly from postgres for CQRS read side.
    """

    def __init__(self, database_url: str) -> None:
        """Initialize repository with database connection string.

        Args:
            database_url: PostgreSQL connection string

        """
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        """Ensure connection pool is created."""
        if self._pool is None:
            import asyncpg

            self._pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        return self._pool

    async def get_by_id(self, config_id: str) -> VectorizationConfigReadModel | None:
        """Get vectorization config by ID.

        Args:
            config_id: Config UUID as string

        Returns:
            VectorizationConfigReadModel or None if not found

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    version,
                    status,
                    description,
                    previous_version_id,
                    chunking_strategy_ids,
                    embedding_strategy_ids,
                    vector_indexing_strategy,
                    vector_similarity_metric,
                    created_at,
                    updated_at
                FROM vectorization_configs
                WHERE id = $1
                """,
                config_id,
            )

            if not row:
                return None

            return VectorizationConfigReadModel(
                id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                version=row["version"],
                status=row["status"],
                description=row["description"],
                previous_version_id=(
                    str(row["previous_version_id"])
                    if row["previous_version_id"]
                    else None
                ),
                chunking_strategy_ids=[str(sid) for sid in row["chunking_strategy_ids"]],
                embedding_strategy_ids=[str(sid) for sid in row["embedding_strategy_ids"]],
                vector_indexing_strategy=row["vector_indexing_strategy"],
                vector_similarity_metric=row["vector_similarity_metric"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_all(
        self, limit: int = 100, offset: int = 0, statuses: list[str] | None = None
    ) -> list[VectorizationConfigReadModel]:
        """Get all vectorization configs with pagination.

        Args:
            limit: Maximum number of items to return
            offset: Number of items to skip
            statuses: Filter by status values (None = no filter)

        Returns:
            List of VectorizationConfigReadModel instances

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            if statuses is None:
                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        version,
                        status,
                        description,
                        previous_version_id,
                        chunking_strategy_ids,
                        embedding_strategy_ids,
                        vector_indexing_strategy,
                        vector_similarity_metric,
                        created_at,
                        updated_at
                    FROM vectorization_configs
                    ORDER BY created_at DESC
                    OFFSET $1 LIMIT $2
                    """,
                    offset,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        version,
                        status,
                        description,
                        previous_version_id,
                        chunking_strategy_ids,
                        embedding_strategy_ids,
                        vector_indexing_strategy,
                        vector_similarity_metric,
                        created_at,
                        updated_at
                    FROM vectorization_configs
                    WHERE status = ANY($1::text[])
                    ORDER BY created_at DESC
                    OFFSET $2 LIMIT $3
                    """,
                    statuses,
                    offset,
                    limit,
                )

            return [
                VectorizationConfigReadModel(
                    id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                    version=row["version"],
                    status=row["status"],
                    description=row["description"],
                    previous_version_id=(
                        str(row["previous_version_id"])
                        if row["previous_version_id"]
                        else None
                    ),
                    chunking_strategy_ids=[str(sid) for sid in row["chunking_strategy_ids"]],
                    embedding_strategy_ids=[str(sid) for sid in row["embedding_strategy_ids"]],
                    vector_indexing_strategy=row["vector_indexing_strategy"],
                    vector_similarity_metric=row["vector_similarity_metric"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def count(self, statuses: list[str] | None = None) -> int:
        """Count total vectorization configs.

        Args:
            statuses: Filter by status values (None = no filter)

        Returns:
            Total count of configs matching filters

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            if statuses is None:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM vectorization_configs
                    """
                )
                return count or 0
            count = await conn.fetchval(
                """
                    SELECT COUNT(*)
                    FROM vectorization_configs
                    WHERE status = ANY($1::text[])
                    """,
                statuses,
            )
            return count or 0

    async def get_by_library(self, library_id: str) -> list[VectorizationConfigReadModel]:
        """Get all vectorization configs associated with a library.

        Args:
            library_id: Library ID (UUID string)

        Returns:
            List of VectorizationConfigReadModel instances associated with the library

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    vc.id,
                    vc.version,
                    vc.status,
                    vc.description,
                    vc.previous_version_id,
                    vc.chunking_strategy_ids,
                    vc.embedding_strategy_ids,
                    vc.vector_indexing_strategy,
                    vc.vector_similarity_metric,
                    vc.created_at,
                    vc.updated_at
                FROM vectorization_configs vc
                INNER JOIN library_vectorization_configs lvc ON vc.id = lvc.vectorization_config_id
                WHERE lvc.library_id = $1
                ORDER BY vc.created_at DESC
                """,
                library_id,
            )

            return [
                VectorizationConfigReadModel(
                    id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                    version=row["version"],
                    status=row["status"],
                    description=row["description"],
                    previous_version_id=(
                        str(row["previous_version_id"])
                        if row["previous_version_id"]
                        else None
                    ),
                    chunking_strategy_ids=[str(sid) for sid in row["chunking_strategy_ids"]],
                    embedding_strategy_ids=[str(sid) for sid in row["embedding_strategy_ids"]],
                    vector_indexing_strategy=row["vector_indexing_strategy"],
                    vector_similarity_metric=row["vector_similarity_metric"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
