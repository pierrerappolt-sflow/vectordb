"""Base query interface for CQRS pattern with generic type parameters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from vdb_core.application.read_repository_provider import ReadRepositoryProvider


class Query[TInput, TOutput](ABC):
    """Base class for all query handlers in the application.

    Queries represent read operations that do not change system state.
    They follow the Query pattern and are part of the CQRS architecture.

    This base class mirrors the Command pattern:
    - execute() orchestrates the read repository provider context
    - _execute() contains the actual query logic (abstract)

    Type Parameters:
        TInput: Type of input data
        TOutput: Type of output data

    Example:
        class GetLibrariesQuery(Query[GetLibrariesInput, list[LibraryReadModel]]):
            async def _execute(
                self, input_data: GetLibrariesInput, read_repo_provider: ReadRepositoryProvider
            ) -> list[LibraryReadModel]:
                return await read_repo_provider.libraries.get_all(
                    limit=input_data.limit, offset=input_data.offset
                )

        # Usage:
        query = GetLibrariesQuery(read_repo_provider_factory)
        libraries = await query.execute(GetLibrariesInput(limit=10))

    """

    def __init__(self, read_repo_provider_factory: Callable[[], ReadRepositoryProvider]) -> None:
        """Initialize query with dependencies.

        Args:
            read_repo_provider_factory: Factory function that creates ReadRepositoryProvider instances

        """
        self.read_repo_provider_factory = read_repo_provider_factory

    async def execute(self, input_data: TInput) -> TOutput:
        """Execute the query with typed input.

        This template method:
        1. Creates a read repository provider
        2. Opens async context
        3. Calls _execute() (implemented by subclasses)
        4. Returns the result

        Args:
            input_data: Typed input data for the query

        Returns:
            Typed output/result data (typically read models)

        Raises:
            Exception: If query execution fails

        """
        read_repo_provider = self.read_repo_provider_factory()
        async with read_repo_provider:
            result = await self._execute(input_data, read_repo_provider)

        return result

    @abstractmethod
    async def _execute(self, input_data: TInput, read_repo_provider: ReadRepositoryProvider) -> TOutput:
        """Execute the query's logic.

        This method is called within a read repository provider context.
        Subclasses implement their query logic here.

        Args:
            input_data: Typed input data for the query
            read_repo_provider: Active read repository provider with all read repositories

        Returns:
            Typed output/result data (typically read models)

        Raises:
            Exception: If query execution fails

        """
        ...
