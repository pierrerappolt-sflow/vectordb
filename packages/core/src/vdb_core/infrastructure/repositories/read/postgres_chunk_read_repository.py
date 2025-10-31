"""PostgreSQL implementation of Chunk read repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import ChunkReadModel
from vdb_core.application.repositories import IChunkReadRepository
from vdb_core.domain.value_objects import ChunkId

if TYPE_CHECKING:
    import asyncpg


class PostgresChunkReadRepository(IChunkReadRepository):
    """PostgreSQL implementation of Chunk read repository.

    Queries chunks directly from postgres for CQRS read side.
    Maps database schema to ChunkReadModel:
    - sequence_number -> used for ordering
    - content -> text
    - modality_type -> metadata

    Uses lazy pool initialization to work with async event loops.
    """

    def __init__(self, database_url: str, shared_pool: asyncpg.Pool | None = None) -> None:
        """Initialize repository.

        Args:
            database_url: PostgreSQL connection string
            shared_pool: Optional shared connection pool (for DI container reuse)

        """
        self.database_url = database_url
        self._pool = shared_pool

    async def _ensure_pool(self) -> asyncpg.Pool:
        """Lazy-create connection pool if not provided."""
        if self._pool is None:
            import asyncpg

            self._pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        return self._pool

    async def get_by_id(self, chunk_id: ChunkId) -> ChunkReadModel | None:
        """Get a chunk by its ID.

        Args:
            chunk_id: Chunk ID value object (contains UUID string in value field)

        Returns:
            ChunkReadModel if found, None otherwise

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    c.id,
                    c.document_id,
                    c.chunking_strategy_id,
                    c.sequence_number,
                    c.content,
                    c.content_hash,
                    c.modality_type,
                    c.created_at,
                    c.updated_at
                FROM chunks c
                WHERE c.id = $1
                """,
                chunk_id.value,  # Use .value to get the actual UUID string
            )

            if not row:
                return None

            return ChunkReadModel(
                id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                document_id=str(row["document_id"]) if not isinstance(row["document_id"], str) else row["document_id"],
                chunking_strategy=str(row["chunking_strategy_id"]),
                text=row["content"],
                status="completed",
                metadata={"modality_type": row["modality_type"], "content_hash": row["content_hash"]},
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_chunks_by_document(
        self, library_id: str, document_id: str, limit: int = 100, offset: int = 0
    ) -> list[ChunkReadModel]:
        """Get all chunks for a document with pagination.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of ChunkReadModel instances ordered by sequence number

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    c.id,
                    c.document_id,
                    c.chunking_strategy_id,
                    c.sequence_number,
                    c.content,
                    c.content_hash,
                    c.modality_type,
                    c.created_at,
                    c.updated_at
                FROM chunks c
                INNER JOIN documents d ON d.id = c.document_id
                WHERE d.library_id = $1 AND c.document_id = $2
                ORDER BY c.sequence_number ASC
                OFFSET $3 LIMIT $4
                """,
                library_id,
                document_id,
                offset,
                limit,
            )

            return [
                ChunkReadModel(
                    id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                    document_id=str(row["document_id"]) if not isinstance(row["document_id"], str) else row["document_id"],
                    chunking_strategy=str(row["chunking_strategy_id"]),
                    text=row["content"],
                    status="completed",
                    metadata={"modality_type": row["modality_type"], "content_hash": row["content_hash"]},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
