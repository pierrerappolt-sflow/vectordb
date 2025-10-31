"""Event log queries for read operations (CQRS pattern)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.base.query import Query
from vdb_core.application.queries import (
    GetEventLogByIdQuery as GetEventLogByIdInput,
)
from vdb_core.application.queries import (
    GetEventLogsQuery as GetEventLogsInput,
)
from vdb_core.application.read_models import EventLogReadModel

if TYPE_CHECKING:
    from vdb_core.application.read_repository_provider import ReadRepositoryProvider


class GetEventLogsQuery(Query[GetEventLogsInput, list[EventLogReadModel]]):
    """Query to get event logs with filtering.

    Following CQRS + Command pattern:
    - Extends Query base class
    - Uses read repository provider
    - Returns read models (DTOs)
    - Supports filtering by event type and aggregate type

    Example:
        query = GetEventLogsQuery(read_repo_provider_factory)
        events = await query.execute(
            GetEventLogsInput(
                event_type="DocumentCreated",
                limit=50
            )
        )

    """

    async def _execute(
        self, input_data: GetEventLogsInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[EventLogReadModel]:
        """Execute the get event logs query.

        Args:
            input_data: The query input with filters and pagination params
            read_repo_provider: Active read repository provider

        Returns:
            List of event log read models ordered by occurred_at descending

        """
        if read_repo_provider.event_logs is None:
            msg = "Event_Logs repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.event_logs.get_all(
            event_type=input_data.event_type,
            aggregate_type=input_data.aggregate_type,
            limit=input_data.limit,
            offset=input_data.offset,
        )


class GetEventLogByIdQuery(Query[GetEventLogByIdInput, EventLogReadModel | None]):
    """Query to get an event log by ID.

    Following CQRS + Command pattern:
    - Handles single event log lookup
    - Returns read model or None
    - No domain logic

    """

    async def _execute(
        self, input_data: GetEventLogByIdInput, read_repo_provider: ReadRepositoryProvider
    ) -> EventLogReadModel | None:
        """Execute the get event log by ID query.

        Args:
            input_data: The query input with event_log_id
            read_repo_provider: Active read repository provider

        Returns:
            Event log read model if found, None otherwise

        """
        if read_repo_provider.event_logs is None:
            msg = "Event logs repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.event_logs.get_by_id(
            event_log_id=input_data.event_log_id,
        )
