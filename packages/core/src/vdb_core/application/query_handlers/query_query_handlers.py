"""Query queries for read operations (CQRS pattern)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.base.query import Query
from vdb_core.application.queries import (
    GetQueriesQuery as GetQueriesInput,
)
from vdb_core.application.queries import (
    GetQueryByIdQuery as GetQueryByIdInput,
)
from vdb_core.application.read_models import QueryReadModel

if TYPE_CHECKING:
    from vdb_core.application.read_repository_provider import ReadRepositoryProvider


class GetQueriesQuery(Query[GetQueriesInput, list[QueryReadModel]]):
    """Query to get all queries in a library.

    Following CQRS + Command pattern:
    - Extends Query base class
    - Uses read repository provider
    - Returns read models (DTOs)
    - No business logic, just data retrieval

    Example:
        query = GetQueriesQuery(read_repo_provider_factory)
        queries = await query.execute(GetQueriesInput(library_id="uuid", limit=10))

    """

    async def _execute(
        self, input_data: GetQueriesInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[QueryReadModel]:
        """Execute the get queries query.

        Args:
            input_data: The query input with library_id and pagination params
            read_repo_provider: Active read repository provider

        Returns:
            List of query read models

        """
        if not read_repo_provider.queries:
            # Query repository not configured
            return []

        return await read_repo_provider.queries.get_all_in_library(
            library_id=input_data.library_id,
            limit=input_data.limit,
            offset=input_data.offset,
        )


class GetQueryByIdQuery(Query[GetQueryByIdInput, QueryReadModel | None]):
    """Query to get a query by ID.

    Following CQRS + Command pattern:
    - Handles single query lookup
    - Returns read model or None
    - No domain logic

    """

    async def _execute(
        self, input_data: GetQueryByIdInput, read_repo_provider: ReadRepositoryProvider
    ) -> QueryReadModel | None:
        """Execute the get query by ID query.

        Args:
            input_data: The query input with library_id and query_id
            read_repo_provider: Active read repository provider

        Returns:
            Query read model if found, None otherwise

        """
        if not read_repo_provider.queries:
            # Query repository not configured
            return None

        return await read_repo_provider.queries.get_by_id(
            library_id=input_data.library_id,
            query_id=input_data.query_id,
        )
