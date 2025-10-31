"""PostgreSQL implementation of DocumentFragment read repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import DocumentFragmentReadModel
from vdb_core.application.repositories import IDocumentFragmentReadRepository

if TYPE_CHECKING:
    import asyncpg


class PostgresDocumentFragmentReadRepository(IDocumentFragmentReadRepository):
    """PostgreSQL implementation of DocumentFragment read repository.

    Queries document fragments directly from postgres for CQRS read side.
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

    async def get_all_in_document(
        self,
        library_id: str,
        document_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DocumentFragmentReadModel]:
        """Get all fragments for a document with pagination.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of DocumentFragmentReadModel instances ordered by sequence_number

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    df.id,
                    df.document_id,
                    df.sequence_number,
                    LENGTH(df.content) as size_bytes,
                    df.content,
                    df.content_hash,
                    df.is_final,
                    df.created_at,
                    df.updated_at
                FROM document_fragments df
                INNER JOIN documents d ON d.id = df.document_id
                WHERE d.library_id = $1 AND df.document_id = $2
                ORDER BY df.sequence_number
                OFFSET $3 LIMIT $4
                """,
                library_id,
                document_id,
                offset,
                limit,
            )

            return [
                DocumentFragmentReadModel(
                    id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                    document_id=str(row["document_id"]) if not isinstance(row["document_id"], str) else row["document_id"],
                    sequence_number=row["sequence_number"],
                    size_bytes=row["size_bytes"],
                    content=row["content"].decode("utf-8", errors="replace") if isinstance(row["content"], bytes) else row["content"],
                    content_hash=row["content_hash"],
                    is_final=row["is_final"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
