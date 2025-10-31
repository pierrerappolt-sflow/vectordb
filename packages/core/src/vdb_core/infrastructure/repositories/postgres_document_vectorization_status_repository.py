"""Postgres implementation of DocumentVectorizationStatus repository."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vdb_core.application.repositories.i_document_vectorization_status_repository import (
    DocumentVectorizationStatusRecord,
    IDocumentVectorizationStatusRepository,
)
from vdb_core.domain.value_objects import DocumentId, VectorizationConfigId

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    import asyncpg


class PostgresDocumentVectorizationStatusRepository(IDocumentVectorizationStatusRepository):
    """Postgres implementation for document vectorization status tracking.

    This repository manages the document_vectorization_status table which tracks
    processing state for Temporal workflows.

    Architecture note:
    - This is infrastructure layer (knows about SQL, asyncpg)
    - Works with simple data structures, not domain entities
    - Focused on tracking/coordination, not business logic
    - Manages its own connection pool like other read repositories
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

    async def upsert(
        self,
        document_id: DocumentId,
        config_id: VectorizationConfigId,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Create or update status entry for document+config pair.

        Args:
            document_id: Document ID
            config_id: Vectorization config ID
            status: Processing status (pending, processing, completed, failed)
            error_message: Optional error message (only for failed status)

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO document_vectorization_status
                    (id, document_id, vectorization_config_id, status, error_message, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), $1, $2, $3, $4, NOW(), NOW())
                ON CONFLICT (document_id, vectorization_config_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message,
                    updated_at = NOW()
                """,
                document_id,
                config_id,
                status,
                error_message,
            )

        logger.debug("Upserted status %s for document %s config %s", status, document_id, config_id)

    async def get(
        self,
        document_id: DocumentId,
        config_id: VectorizationConfigId,
    ) -> DocumentVectorizationStatusRecord | None:
        """Get status for specific document+config pair.

        Args:
            document_id: Document ID
            config_id: Vectorization config ID

        Returns:
            Status record if found, None otherwise

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    document_id,
                    vectorization_config_id as config_id,
                    status,
                    error_message,
                    created_at,
                    updated_at
                FROM document_vectorization_status
                WHERE document_id = $1 AND vectorization_config_id = $2
                """,
                document_id,
                config_id,
            )

            if not row:
                return None

            return DocumentVectorizationStatusRecord(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                config_id=str(row["config_id"]),
                status=row["status"],
                error_message=row["error_message"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_by_document(
        self,
        document_id: DocumentId,
    ) -> list[DocumentVectorizationStatusRecord]:
        """Get all status entries for a document across all configs.

        Args:
            document_id: Document ID

        Returns:
            List of status records

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    document_id,
                    vectorization_config_id as config_id,
                    status,
                    error_message,
                    created_at,
                    updated_at
                FROM document_vectorization_status
                WHERE document_id = $1
                ORDER BY created_at DESC
                """,
                document_id,
            )

            return [
                DocumentVectorizationStatusRecord(
                    id=str(row["id"]),
                    document_id=str(row["document_id"]),
                    config_id=str(row["config_id"]),
                    status=row["status"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def list_by_config(
        self,
        config_id: VectorizationConfigId,
    ) -> list[DocumentVectorizationStatusRecord]:
        """Get all status entries for a config across all documents.

        Args:
            config_id: Vectorization config ID

        Returns:
            List of status records

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    document_id,
                    vectorization_config_id as config_id,
                    status,
                    error_message,
                    created_at,
                    updated_at
                FROM document_vectorization_status
                WHERE vectorization_config_id = $1
                ORDER BY created_at DESC
                """,
                config_id,
            )

            return [
                DocumentVectorizationStatusRecord(
                    id=str(row["id"]),
                    document_id=str(row["document_id"]),
                    config_id=str(row["config_id"]),
                    status=row["status"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def list_pending(
        self,
        limit: int = 100,
    ) -> list[DocumentVectorizationStatusRecord]:
        """Get pending status entries for workflow scheduling.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of pending status records

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    document_id,
                    vectorization_config_id as config_id,
                    status,
                    error_message,
                    created_at,
                    updated_at
                FROM document_vectorization_status
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT $1
                """,
                limit,
            )

            return [
                DocumentVectorizationStatusRecord(
                    id=str(row["id"]),
                    document_id=str(row["document_id"]),
                    config_id=str(row["config_id"]),
                    status=row["status"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
