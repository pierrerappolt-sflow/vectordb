"""PostgreSQL implementation of Library read repository."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from vdb_core.application.read_models import LibraryReadModel
from vdb_core.application.repositories import ILibraryReadRepository
from vdb_core.domain.exceptions import LibraryNotFoundError

if TYPE_CHECKING:
    import asyncpg


class PostgresLibraryReadRepository(ILibraryReadRepository):
    """PostgreSQL implementation of Library read repository.

    Queries libraries directly from postgres for CQRS read side.
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

    async def get_by_id(self, library_id: str) -> LibraryReadModel:
        """Get library by ID (excludes DELETED libraries).

        Args:
            library_id: Library UUID as string

        Returns:
            Library read model

        Raises:
            LibraryNotFoundError: If library not found or deleted

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    l.id,
                    l.name,
                    l.status,
                    l.created_at,
                    l.updated_at,
                    COUNT(DISTINCT d.id) as document_count
                FROM libraries l
                LEFT JOIN documents d ON d.library_id = l.id
                WHERE l.id = $1 AND l.status != 'deleted'
                GROUP BY l.id, l.name, l.status, l.created_at, l.updated_at
                """,
                library_id,
            )

            if not row:
                raise LibraryNotFoundError(f"Library {library_id} not found")

            return LibraryReadModel(
                id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                name=row["name"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                document_count=row["document_count"] or 0,
            )

    async def list(self, skip: int = 0, limit: int = 100) -> builtins.list[LibraryReadModel]:
        """List all libraries with pagination (excludes DELETED libraries).

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of library read models (excluding deleted)

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    l.id,
                    l.name,
                    l.status,
                    l.created_at,
                    l.updated_at,
                    COUNT(DISTINCT d.id) as document_count
                FROM libraries l
                LEFT JOIN documents d ON d.library_id = l.id
                WHERE l.status != 'deleted'
                GROUP BY l.id, l.name, l.status, l.created_at, l.updated_at
                ORDER BY l.created_at DESC
                OFFSET $1 LIMIT $2
                """,
                skip,
                limit,
            )

            return [
                LibraryReadModel(
                    id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                    name=row["name"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    document_count=row["document_count"] or 0,
                )
                for row in rows
            ]

    async def count(self) -> int:
        """Count total number of libraries (excludes DELETED libraries).

        Returns:
            Total count of non-deleted libraries

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM libraries WHERE status != 'deleted'")
            return count or 0

    async def get_all(self, limit: int = 100, offset: int = 0) -> builtins.list[LibraryReadModel]:
        """Get all libraries with pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of LibraryReadModel instances

        """
        return await self.list(skip=offset, limit=limit)

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
