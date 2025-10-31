"""Library queries for read operations (CQRS pattern)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.base.query import Query
from vdb_core.application.queries import (
    GetLibrariesQuery as GetLibrariesInput,
)
from vdb_core.application.queries import (
    GetLibraryByIdQuery as GetLibraryByIdInput,
)
from vdb_core.application.queries import (
    GetLibraryConfigsQuery as GetLibraryConfigsInput,
)
from vdb_core.application.read_models import LibraryReadModel, VectorizationConfigReadModel

if TYPE_CHECKING:
    from vdb_core.application.read_repository_provider import ReadRepositoryProvider


class GetLibrariesQuery(Query[GetLibrariesInput, list[LibraryReadModel]]):
    """Query to get all libraries.

    Following CQRS + Command pattern:
    - Extends Query base class
    - Uses read repository provider
    - Returns read models (DTOs)
    - No business logic, just data retrieval

    Example:
        query = GetLibrariesQuery(read_repo_provider_factory)
        libraries = await query.execute(GetLibrariesInput(limit=10))

    """

    async def _execute(
        self, input_data: GetLibrariesInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[LibraryReadModel]:
        """Execute the get libraries query.

        Args:
            input_data: The query input with pagination params
            read_repo_provider: Active read repository provider

        Returns:
            List of library read models

        """
        if read_repo_provider.libraries is None:
            msg = "Libraries repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.libraries.get_all(limit=input_data.limit, offset=input_data.offset)


class GetLibraryByIdQuery(Query[GetLibraryByIdInput, LibraryReadModel]):
    """Query to get a library by ID.

    Following CQRS + Command pattern:
    - Handles single library lookup
    - Returns read model or raises error
    - No domain logic

    """

    async def _execute(
        self, input_data: GetLibraryByIdInput, read_repo_provider: ReadRepositoryProvider
    ) -> LibraryReadModel:
        """Execute the get library by ID query.

        Args:
            input_data: The query input with library ID
            read_repo_provider: Active read repository provider

        Returns:
            Library read model

        Raises:
            LibraryNotFoundError: If library not found

        """
        if read_repo_provider.libraries is None:
            msg = "Libraries repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.libraries.get_by_id(input_data.library_id)


class GetLibraryConfigsQuery(Query[GetLibraryConfigsInput, list[VectorizationConfigReadModel]]):
    """Query to get all vectorization configs for a library.

    Following CQRS + Command pattern:
    - Handles read-only queries
    - Uses vectorization config read repository
    - Returns list of config read models
    - No business logic

    """

    async def _execute(
        self, input_data: GetLibraryConfigsInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[VectorizationConfigReadModel]:
        """Execute the get library configs query.

        Args:
            input_data: The query input with library ID
            read_repo_provider: Active read repository provider

        Returns:
            List of vectorization config read models for the library

        """
        if read_repo_provider.vectorization_configs is None:
            msg = "Vectorization configs repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.vectorization_configs.get_by_library(input_data.library_id)
