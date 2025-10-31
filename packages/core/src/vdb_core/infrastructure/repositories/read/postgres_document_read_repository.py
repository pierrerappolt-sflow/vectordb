"""PostgreSQL implementation of Document read repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import (
    DocumentFragmentReadModel,
    DocumentReadModel,
    DocumentVectorizationStatusReadModel,
)
from vdb_core.application.repositories import IDocumentReadRepository

if TYPE_CHECKING:
    import asyncpg


class PostgresDocumentReadRepository(IDocumentReadRepository):
    """PostgreSQL implementation of Document read repository.

    Queries documents directly from postgres for CQRS read side.
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

    async def get_by_id(self, library_id: str, document_id: str) -> DocumentReadModel | None:
        """Get document by ID.

        Args:
            library_id: Library ID (UUID string)
            document_id: Document ID (UUID string)

        Returns:
            DocumentReadModel if found, None otherwise

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH doc AS (
                    SELECT * FROM documents d WHERE d.library_id = $1 AND d.id = $2
                ),
                frags AS (
                    SELECT
                        df.id,
                        df.document_id,
                        df.sequence_number,
                        LENGTH(df.content) as size_bytes,
                        convert_from(df.content, 'UTF8') as content,
                        df.content_hash,
                        df.is_final,
                        df.created_at,
                        df.updated_at
                    FROM document_fragments df
                    WHERE df.document_id = $2
                    ORDER BY df.sequence_number
                ),
                statuses AS (
                    SELECT
                        dvs.id,
                        dvs.document_id,
                        dvs.vectorization_config_id,
                        dvs.status,
                        dvs.error_message,
                        dvs.created_at,
                        dvs.updated_at
                    FROM document_vectorization_status dvs
                    WHERE dvs.document_id = $2
                ),
                embeddings_count_cte AS (
                    SELECT COUNT(DISTINCT e.id) as embeddings_count
                    FROM embeddings e
                    INNER JOIN chunks c ON e.chunk_id = c.id
                    WHERE c.document_id = $2
                ),
                embeddings_by_config AS (
                    SELECT
                        e.vectorization_config_id::text as config_id,
                        COUNT(DISTINCT e.id) as embedding_count
                    FROM chunks c
                    INNER JOIN embeddings e ON e.chunk_id = c.id
                    WHERE c.document_id = $2
                    GROUP BY e.vectorization_config_id
                )
                SELECT
                    doc.id,
                    doc.library_id,
                    doc.name,
                    doc.status,
                    doc.upload_complete,
                    doc.created_at,
                    doc.updated_at,
                    (SELECT COUNT(*) FROM frags) as fragment_count,
                    (SELECT COALESCE(SUM(size_bytes), 0) FROM frags) as total_bytes,
                    COALESCE((SELECT embeddings_count FROM embeddings_count_cte), 0) as embeddings_count,
                    COALESCE(
                        (SELECT json_object_agg(ebc.config_id, ebc.embedding_count)
                         FROM embeddings_by_config ebc),
                        '{}'::json
                    ) as embeddings_by_config_id,
                    COALESCE(
                        (SELECT json_agg(
                            json_build_object(
                                'id', s.id,
                                'document_id', s.document_id,
                                'config_id', s.vectorization_config_id,
                                'status', s.status,
                                'error_message', s.error_message,
                                'created_at', s.created_at,
                                'updated_at', s.updated_at
                            ) ORDER BY s.created_at
                        ) FROM statuses s),
                        '[]'::json
                    ) as vectorization_statuses,
                    COALESCE(
                        (SELECT json_agg(
                            json_build_object(
                                'id', f.id,
                                'document_id', f.document_id,
                                'sequence_number', f.sequence_number,
                                'size_bytes', f.size_bytes,
                                'content', f.content,
                                'content_hash', f.content_hash,
                                'is_final', f.is_final,
                                'created_at', f.created_at,
                                'updated_at', f.updated_at
                            ) ORDER BY f.sequence_number
                        ) FROM frags f),
                        '[]'::json
                    ) as fragments
                FROM doc
                """,
                library_id,
                document_id,
            )

            if not row:
                return None

            # Parse vectorization statuses and fragments from JSON aggregation
            import json

            vectorization_statuses = []
            if row["vectorization_statuses"]:
                statuses_data = row["vectorization_statuses"]
                if isinstance(statuses_data, str):
                    statuses_data = json.loads(statuses_data)

                for status_row in statuses_data:
                    vectorization_statuses.append(
                        DocumentVectorizationStatusReadModel(
                            id=str(status_row["id"]),
                            document_id=str(status_row["document_id"]),
                            config_id=str(status_row["config_id"]),
                            status=status_row["status"],
                            error_message=status_row.get("error_message"),
                            created_at=status_row["created_at"],
                            updated_at=status_row["updated_at"],
                        )
                    )

            fragments = []
            if row["fragments"]:
                fragments_data = row["fragments"]
                if isinstance(fragments_data, str):
                    fragments_data = json.loads(fragments_data)

                for frag_row in fragments_data:
                    fragments.append(
                        DocumentFragmentReadModel(
                            id=str(frag_row["id"]),
                            document_id=str(frag_row["document_id"]),
                            sequence_number=frag_row["sequence_number"],
                            size_bytes=frag_row["size_bytes"],
                            content=frag_row["content"],
                            content_hash=frag_row["content_hash"],
                            is_final=frag_row["is_final"],
                            created_at=frag_row["created_at"],
                            updated_at=frag_row["updated_at"],
                        )
                    )

            # Parse embeddings_by_config_id from JSON
            embeddings_by_config_id = {}
            if row["embeddings_by_config_id"]:
                embeddings_data = row["embeddings_by_config_id"]
                if isinstance(embeddings_data, str):
                    embeddings_data = json.loads(embeddings_data)
                embeddings_by_config_id = embeddings_data

            return DocumentReadModel(
                id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                library_id=str(row["library_id"]) if not isinstance(row["library_id"], str) else row["library_id"],
                name=row["name"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                upload_complete=row["upload_complete"],
                fragment_count=row["fragment_count"] or 0,
                total_bytes=row["total_bytes"] or 0,
                embeddings_count=row["embeddings_count"] or 0,
                embeddings_by_config_id=embeddings_by_config_id,
                vectorization_statuses=vectorization_statuses,
                fragments=fragments,
            )

    async def get_all_in_library(self, library_id: str, limit: int = 100, offset: int = 0) -> list[DocumentReadModel]:
        """Get all documents in a library with pagination.

        Args:
            library_id: Library ID (UUID string)
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of DocumentReadModel instances

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH embeddings_by_config_per_doc AS (
                    SELECT
                        c.document_id,
                        e.vectorization_config_id::text as config_id,
                        COUNT(DISTINCT e.id) as embedding_count
                    FROM chunks c
                    INNER JOIN embeddings e ON e.chunk_id = c.id
                    WHERE c.document_id IN (SELECT id FROM documents WHERE library_id = $1)
                    GROUP BY c.document_id, e.vectorization_config_id
                )
                SELECT
                    d.id,
                    d.library_id,
                    d.name,
                    d.status,
                    d.upload_complete,
                    d.created_at,
                    d.updated_at,
                    COUNT(DISTINCT df.id) as fragment_count,
                    COALESCE(SUM(LENGTH(df.content)), 0) as total_bytes,
                    COUNT(DISTINCT e.id) as embeddings_count,
                    COALESCE(
                        (SELECT json_object_agg(ebc.config_id, ebc.embedding_count)
                         FROM embeddings_by_config_per_doc ebc
                         WHERE ebc.document_id = d.id),
                        '{}'::json
                    ) as embeddings_by_config_id,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', dvs.id,
                                'document_id', dvs.document_id,
                                'config_id', dvs.vectorization_config_id,
                                'status', dvs.status,
                                'error_message', dvs.error_message,
                                'created_at', dvs.created_at,
                                'updated_at', dvs.updated_at
                            ) ORDER BY dvs.created_at
                        ) FILTER (WHERE dvs.id IS NOT NULL),
                        '[]'::json
                    ) as vectorization_statuses
                FROM documents d
                LEFT JOIN document_fragments df ON df.document_id = d.id
                LEFT JOIN document_vectorization_status dvs ON dvs.document_id = d.id
                LEFT JOIN chunks c ON c.document_id = d.id
                LEFT JOIN embeddings e ON e.chunk_id = c.id
                WHERE d.library_id = $1
                GROUP BY d.id, d.library_id, d.name, d.status, d.upload_complete, d.created_at, d.updated_at
                ORDER BY d.created_at DESC
                OFFSET $2 LIMIT $3
                """,
                library_id,
                offset,
                limit,
            )

            import json

            results = []
            for row in rows:
                # Parse vectorization statuses from JSON aggregation
                vectorization_statuses = []
                if row["vectorization_statuses"]:
                    statuses_data = row["vectorization_statuses"]
                    if isinstance(statuses_data, str):
                        statuses_data = json.loads(statuses_data)

                    for status_row in statuses_data:
                        vectorization_statuses.append(
                            DocumentVectorizationStatusReadModel(
                                id=str(status_row["id"]),
                                document_id=str(status_row["document_id"]),
                                config_id=str(status_row["config_id"]),
                                status=status_row["status"],
                                error_message=status_row.get("error_message"),
                                created_at=status_row["created_at"],
                                updated_at=status_row["updated_at"],
                            )
                        )

                # Parse embeddings_by_config_id from JSON
                embeddings_by_config_id = {}
                if row["embeddings_by_config_id"]:
                    embeddings_data = row["embeddings_by_config_id"]
                    if isinstance(embeddings_data, str):
                        embeddings_data = json.loads(embeddings_data)
                    embeddings_by_config_id = embeddings_data

                results.append(
                    DocumentReadModel(
                        id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                        library_id=str(row["library_id"]) if not isinstance(row["library_id"], str) else row["library_id"],
                        name=row["name"],
                        status=row["status"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        upload_complete=row["upload_complete"],
                        fragment_count=row["fragment_count"] or 0,
                        total_bytes=row["total_bytes"] or 0,
                        embeddings_count=row["embeddings_count"] or 0,
                        embeddings_by_config_id=embeddings_by_config_id,
                        vectorization_statuses=vectorization_statuses,
                    )
                )

            return results

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
