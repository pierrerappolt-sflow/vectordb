"""PostgreSQL implementation of EventLog read repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.read_models import EventLogReadModel
from vdb_core.application.repositories import IEventLogReadRepository

if TYPE_CHECKING:
    import asyncpg


class PostgresEventLogReadRepository(IEventLogReadRepository):
    """PostgreSQL implementation of EventLog read repository.

    Queries event logs directly from postgres for CQRS read side.
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

    async def get_by_id(self, event_log_id: str) -> EventLogReadModel | None:
        """Get event log entry by ID.

        Args:
            event_log_id: EventLog ID (UUID string)

        Returns:
            EventLogReadModel if found, None otherwise

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    event_type,
                    library_id as aggregate_id,
                    'Library' as aggregate_type,
                    data as payload,
                    timestamp as occurred_at,
                    created_at
                FROM event_logs
                WHERE id = $1
                """,
                event_log_id,
            )

            if not row:
                return None

            return EventLogReadModel(
                id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                event_type=row["event_type"],
                aggregate_id=str(row["aggregate_id"]) if row["aggregate_id"] else "",
                aggregate_type=row["aggregate_type"],
                payload=row["payload"] if isinstance(row["payload"], dict) else {},
                occurred_at=row["occurred_at"],
                created_at=row["created_at"],
            )

    async def get_all(
        self,
        event_type: str | None = None,
        aggregate_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventLogReadModel]:
        """Get all event logs across all libraries.

        Args:
            event_type: Optional event type filter (e.g., "DocumentCreated")
            aggregate_type: Optional aggregate type filter (e.g., "Document")
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of EventLogReadModel instances ordered by occurred_at descending

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            # Build query with optional filters
            query = """
                SELECT
                    id,
                    event_type,
                    COALESCE(library_id, document_id) as aggregate_id,
                    CASE
                        WHEN library_id IS NOT NULL THEN 'Library'
                        WHEN document_id IS NOT NULL THEN 'Document'
                        ELSE 'Unknown'
                    END as aggregate_type,
                    data as payload,
                    timestamp as occurred_at,
                    created_at
                FROM event_logs
            """
            params: list[object] = []
            param_count = 0
            where_clauses = []

            if event_type:
                param_count += 1
                where_clauses.append(f"event_type = ${param_count}")
                params.append(event_type)

            if aggregate_type:
                if aggregate_type == "Library":
                    where_clauses.append("library_id IS NOT NULL")
                elif aggregate_type == "Document":
                    where_clauses.append("document_id IS NOT NULL")

            # Add WHERE clause if we have any filters
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY timestamp DESC"
            param_count += 1
            query += f" OFFSET ${param_count}"
            params.append(offset)
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)

            rows = await conn.fetch(query, *params)

            return [
                EventLogReadModel(
                    id=str(row["id"]) if not isinstance(row["id"], str) else row["id"],
                    event_type=row["event_type"],
                    aggregate_id=str(row["aggregate_id"]) if row["aggregate_id"] else "",
                    aggregate_type=row["aggregate_type"],
                    payload=row["payload"] if isinstance(row["payload"], dict) else {},
                    occurred_at=row["occurred_at"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def count(
        self,
        event_type: str | None = None,
        aggregate_type: str | None = None,
    ) -> int:
        """Count total event logs across all libraries.

        Args:
            event_type: Optional event type filter
            aggregate_type: Optional aggregate type filter

        Returns:
            Total count of matching events

        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            # Build query with optional filters
            query = "SELECT COUNT(*) FROM event_logs"
            params = []
            param_count = 0
            where_clauses = []

            if event_type:
                param_count += 1
                where_clauses.append(f"event_type = ${param_count}")
                params.append(event_type)

            if aggregate_type:
                if aggregate_type == "Library":
                    where_clauses.append("library_id IS NOT NULL")
                elif aggregate_type == "Document":
                    where_clauses.append("document_id IS NOT NULL")

            # Add WHERE clause if we have any filters
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            count = await conn.fetchval(query, *params)
            return count or 0

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
